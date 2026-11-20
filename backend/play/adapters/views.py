import json
import re
from datetime import datetime, timezone

from django.db import transaction
from django.http import JsonResponse
from django.utils import timezone as django_timezone
from django.views.decorators.http import require_GET, require_POST

from challenges.adapters.views import _challenge_summary
from challenges.models import Challenge
from challenges.serialization import media_url
from play.adapters.vector_tone_matcher import VectorToneMatcher
from play.domain.answer_matching import AnswerMatching
from play.domain.star_rules import StarRules
from play.models import ChallengeRun
from play.adapters.errors import RunForbidden, RunNotFound
from tone.adapters.errors import ToneAnswerUnknown, ToneUnavailable
from users.models import ChallengeAttempt, UserProfile


def _json_body(request):
    if request.content_type != "application/json":
        raise ValueError("Expected an application/json body.")
    try:
        value = json.loads(request.body)
    except (ValueError, UnicodeDecodeError) as exc:
        raise ValueError("Expected a valid JSON object.") from exc
    if not isinstance(value, dict):
        raise ValueError("Expected a JSON object.")
    return value


def _node_map(challenge):
    result = {}

    def visit(node):
        result[node["node_key"]] = node
        for child in node.get("children", []):
            visit(child)

    visit(challenge.conversation_tree)
    return result


def _present_node(node, choice_id=None):
    result = {
        "id": node["node_key"],
        "type": node["type"],
        "transcript_url": media_url(node["text_file"]),
        "audio_url": media_url(node["audio_file"]),
    }
    if choice_id is not None:
        result["choice_id"] = str(choice_id)
    return result


def _snapshot(run):
    challenge = run.challenge
    nodes = _node_map(challenge)
    root = challenge.conversation_tree
    history = [_present_node(nodes[key]) for key in run.conversation]
    if run.stage == "tone":
        choices = []
    else:
        current = nodes.get(run.current_node, root)
        choices = [
            _present_node(node, index)
            for index, node in enumerate(current.get("children", []))
            if node["type"] == "response"
        ]
    payload = {
        "attempt_id": str(run.pk),
        "stage": run.stage,
        "challenge": _challenge_summary(challenge),
        "opening": _present_node(root),
        "conversation": history,
        "choices": choices,
        "tone_correct": run.tone_correct,
        "tone_time": run.tone_time,
        "tone_speed_correct": (
            run.tone_time <= 10 if run.tone_time is not None else None
        ),
    }
    if run.tone_similarity is not None:
        payload["tone_similarity"] = run.tone_similarity
    if run.stage == "completed":
        payload.update(
            {
                "action_correct": run.action_correct,
                "score": run.score,
                "required_action": challenge.required_action,
                "completed_at": run.completed_at.isoformat(),
            }
        )
    return payload


def _get_run(attempt_id, request):
    try:
        run = ChallengeRun.objects.select_related("challenge").get(pk=attempt_id)
    except ChallengeRun.DoesNotExist, ValueError:
        raise RunNotFound from None
    if run.user_id is not None and run.user_id != getattr(request.user, "pk", None):
        raise RunForbidden("This attempt belongs to another account.")
    return run


@require_POST
def start_challenge(request, slug):
    """POST /api/challenges/<slug>/attempts/: start a run and return its opening turn."""
    try:
        payload = _json_body(request)
    except ValueError as exc:
        return JsonResponse({"detail": str(exc)}, status=400)
    if payload:
        return JsonResponse({"detail": "Expected an empty JSON object."}, status=400)
    challenge = Challenge.objects.filter(slug=slug).first()
    if challenge is None:
        return JsonResponse({"detail": "Challenge not found."}, status=404)
    run = ChallengeRun.objects.create(
        challenge=challenge,
        user=request.user if request.user.is_authenticated else None,
        current_node=challenge.conversation_tree["node_key"],
    )
    return JsonResponse(_snapshot(run), status=201)


@require_GET
def get_run(request, attempt_id):
    """GET /api/attempts/<uuid>/: return the current run snapshot."""
    try:
        return JsonResponse(_snapshot(_get_run(attempt_id, request)))
    except RunNotFound:
        return JsonResponse({"detail": "Attempt not found."}, status=404)
    except RunForbidden as exc:
        return JsonResponse({"detail": str(exc)}, status=403)


def _transition(request, attempt_id, stage, handler):
    try:
        payload = _json_body(request)
    except ValueError as exc:
        return JsonResponse({"detail": str(exc)}, status=400)
    try:
        run = _get_run(attempt_id, request)
    except RunNotFound:
        return JsonResponse({"detail": "Attempt not found."}, status=404)
    except RunForbidden as exc:
        return JsonResponse({"detail": str(exc)}, status=403)
    if run.stage != stage:
        return JsonResponse({"detail": "Invalid attempt stage transition."}, status=409)
    try:
        handler(run, payload)
    except ToneAnswerUnknown as exc:
        return JsonResponse({"detail": str(exc)}, status=404)
    except ToneUnavailable as exc:
        return JsonResponse({"detail": str(exc)}, status=503)
    except ValueError as exc:
        return JsonResponse({"detail": str(exc)}, status=400)
    run.save()
    if run.stage == "completed" and run.user_id is not None:
        with transaction.atomic():
            profile = UserProfile.objects.select_for_update().get(user_id=run.user_id)
            ChallengeAttempt.objects.get_or_create(
                submission_id=str(run.pk),
                defaults={
                    "profile": profile,
                    "challenge_id": run.challenge_id,
                    "score": run.score,
                    "completed_at": run.completed_at,
                },
            )
            profile.scores = {
                **profile.scores,
                run.challenge_id: max(
                    profile.scores.get(run.challenge_id, 0), run.score
                ),
            }
            profile.recalculate_total()
            profile.save(update_fields=["scores", "total_score", "updated_at"])
    return JsonResponse(_snapshot(run))


@require_POST
def submit_tone(request, attempt_id):
    """POST /api/attempts/<uuid>/tone/: grade the tone and return available responses."""

    def apply(run, payload):
        if set(payload) != {"answer"} or not isinstance(payload["answer"], str):
            raise ValueError("answer must be a string.")
        matcher = VectorToneMatcher()
        similarity = matcher.similarity(payload["answer"], run.challenge.tone)
        elapsed = max(0.0, (django_timezone.now() - run.created_at).total_seconds())
        run.tone_time = elapsed
        run.tone_similarity = similarity
        run.tone_correct = AnswerMatching.tone_is_correct(similarity)
        run.stage = "conversation"
        run.current_node = run.challenge.conversation_tree["node_key"]
        run.conversation = [run.current_node]

    return _transition(request, attempt_id, "tone", apply)


@require_POST
def choose_response(request, attempt_id):
    """POST /api/attempts/<uuid>/choices/: select a response and return the next turn."""

    def apply(run, payload):
        if set(payload) != {"choice_id"} or not isinstance(payload["choice_id"], str):
            raise ValueError("choice_id must be a string.")
        nodes = _node_map(run.challenge)
        current = nodes[run.current_node]
        choices = [
            node for node in current.get("children", []) if node["type"] == "response"
        ]
        raw_index = payload["choice_id"]
        if not re.fullmatch(r"\d+", raw_index) or int(raw_index) >= len(choices):
            raise ValueError("The selected choice is unavailable.")
        response_node = choices[int(raw_index)]
        run.conversation = [*run.conversation, response_node["node_key"]]
        followups = [
            node
            for node in response_node.get("children", [])
            if node["type"] == "question"
        ]
        if followups:
            followup = followups[0]
            run.conversation.append(followup["node_key"])
            run.current_node = followup["node_key"]
        else:
            run.current_node = response_node["node_key"]

    return _transition(request, attempt_id, "conversation", apply)


@require_POST
def continue_conversation(request, attempt_id):
    """POST /api/attempts/<uuid>/continue/: advance to the action stage."""

    def apply(run, payload):
        if payload:
            raise ValueError("Expected an empty JSON object.")
        nodes = _node_map(run.challenge)
        current = nodes[run.current_node]
        if any(node["type"] == "response" for node in current.get("children", [])):
            raise ValueError("Available responses must be selected first.")
        run.stage = "action"

    return _transition(request, attempt_id, "conversation", apply)


@require_POST
def submit_action(request, attempt_id):
    """POST /api/attempts/<uuid>/action/: grade the action and complete the run."""

    def apply(run, payload):
        if set(payload) != {"answer"} or not isinstance(payload["answer"], str):
            raise ValueError("answer must be a string.")
        run.action_correct = AnswerMatching.action_is_correct(
            run.challenge.required_action, payload["answer"]
        )
        run.score = StarRules().score(
            run.tone_correct, run.tone_time, run.action_correct
        )
        run.completed_at = datetime.now(timezone.utc)
        run.stage = "completed"

    return _transition(request, attempt_id, "action", apply)
