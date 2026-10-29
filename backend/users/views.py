import json
from math import isfinite
from uuid import UUID

from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError, transaction
from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from challenges.models import Challenge

from .forms import SignupForm
from .models import ChallengeAttempt, UserProfile


def _auth_payload(request):
    if request.content_type != "application/json":
        raise ValueError("Expected an application/json body.")
    try:
        payload = json.loads(request.body)
    except (ValueError, UnicodeDecodeError) as exc:
        raise ValueError("Expected a valid JSON object.") from exc
    if not isinstance(payload, dict):
        raise ValueError("Expected a JSON object.")
    for field in ("username", "password", "email"):
        if field in payload and not isinstance(payload[field], str):
            raise ValueError(f"{field} must be a string.")
    for field in ("username", "password"):
        if not payload.get(field):
            raise ValueError(f"{field} is required.")
    return payload


def _auth_response(request, status=200):
    user = request.user
    return JsonResponse(
        {
            "user": {"id": user.pk, "username": user.username, "email": user.email},
            "csrfToken": get_token(request),
        },
        status=status,
    )


@never_cache
@require_GET
def csrf_token(request):
    return JsonResponse({"csrfToken": get_token(request)})


@never_cache
@require_POST
def signup(request):
    try:
        payload = _auth_payload(request)
    except ValueError as exc:
        return JsonResponse({"detail": str(exc)}, status=400)
    form = SignupForm(
        data={
            "username": payload["username"],
            "email": payload.get("email", ""),
            "password1": payload["password"],
            "password2": payload["password"],
        }
    )
    if not form.is_valid():
        errors = {}
        for field, messages in form.errors.items():
            key = "password" if field in ("password1", "password2") else field
            errors.setdefault(key, []).extend(messages)
        return JsonResponse({"errors": errors}, status=400)
    try:
        with transaction.atomic():
            user = form.save()
    except IntegrityError:
        return JsonResponse(
            {"errors": {"username": ["A user with that username already exists."]}},
            status=400,
        )
    login(request, user)
    return _auth_response(request, status=201)


@never_cache
@require_POST
def login_user(request):
    try:
        payload = _auth_payload(request)
    except ValueError as exc:
        return JsonResponse({"detail": str(exc)}, status=400)
    user = authenticate(
        request, username=payload["username"], password=payload["password"]
    )
    if user is None:
        return JsonResponse({"detail": "Invalid username or password."}, status=401)
    login(request, user)
    return _auth_response(request)


@never_cache
@require_POST
def logout_user(request):
    logout(request)
    return JsonResponse({"detail": "Logged out."})


@never_cache
@require_GET
def current_user(request):
    if not request.user.is_authenticated:
        return JsonResponse({"detail": "Authentication required."}, status=401)
    return _auth_response(request)


@require_GET
def user_profile(request, user_id):
    profile = get_object_or_404(
        UserProfile.objects.select_related("user"), user__pk=user_id
    )
    return JsonResponse(_profile_data(profile))


def _profile_data(profile):
    return {
        "user_id": profile.user_id,
        "username": profile.user.username,
        "avatar": profile.avatar,
        "total_score": profile.total_score,
        "completed_challenges": len(profile.scores),
        "scores": profile.scores,
    }


@never_cache
@require_POST
def save_challenge_score(request, challenge_id):
    if not request.user.is_authenticated:
        return JsonResponse({"detail": "Authentication required."}, status=401)
    if request.content_type != "application/json":
        return JsonResponse(
            {"detail": "Expected an application/json body."}, status=400
        )
    try:
        payload = json.loads(request.body)
    except ValueError, UnicodeDecodeError:
        return JsonResponse({"detail": "Expected a valid JSON object."}, status=400)
    if not isinstance(payload, dict):
        return JsonResponse({"detail": "Expected a JSON object."}, status=400)
    if not all(
        isinstance(payload.get(key), bool) for key in ("tone_correct", "action_correct")
    ):
        return JsonResponse(
            {"detail": "tone_correct and action_correct must be booleans."}, status=400
        )
    tone_time = payload.get("tone_time")
    if (
        isinstance(tone_time, bool)
        or not isinstance(tone_time, (int, float))
        or (isinstance(tone_time, float) and not isfinite(tone_time))
        or tone_time < 0
    ):
        return JsonResponse(
            {"detail": "tone_time must be a finite, non-negative number of seconds."},
            status=400,
        )
    try:
        if not isinstance(payload.get("attempt_id"), str):
            raise ValueError
        attempt_id = str(UUID(payload["attempt_id"]))
        if not isinstance(payload.get("completed_at"), str):
            raise ValueError
        completed_at = parse_datetime(payload["completed_at"])
        if completed_at is None or timezone.is_naive(completed_at):
            raise ValueError
    except ValueError, TypeError:
        return JsonResponse(
            {
                "detail": "A valid attempt_id UUID and timezone-aware completed_at timestamp are required."
            },
            status=400,
        )
    if not Challenge.objects.filter(pk=challenge_id).exists():
        return JsonResponse({"detail": "Challenge not found."}, status=404)

    stars = (
        int(payload["tone_correct"])
        + int(tone_time <= 10)
        + int(payload["action_correct"])
    )
    score = round(stars * 100 / 3)
    with transaction.atomic():
        profile = (
            UserProfile.objects.select_for_update()
            .select_related("user")
            .get(user=request.user)
        )
        attempt, created = ChallengeAttempt.objects.get_or_create(
            submission_id=attempt_id,
            defaults={
                "profile": profile,
                "challenge_id": challenge_id,
                "score": score,
                "completed_at": completed_at,
            },
        )
        if (
            attempt.profile_id != profile.pk
            or attempt.challenge_id != challenge_id
            or attempt.score != score
            or attempt.completed_at != completed_at
        ):
            return JsonResponse(
                {
                    "detail": "This attempt ID has already been used for a different completion."
                },
                status=409,
            )
        profile.add_score(
            challenge_id, max(profile.scores.get(str(challenge_id), 0), score)
        )
        profile.save(update_fields=["scores", "total_score", "updated_at"])
    return JsonResponse(
        {
            **_profile_data(profile),
            "attempt": {
                "id": attempt.pk,
                "attempt_id": attempt.submission_id,
                "challenge_id": attempt.challenge_id,
                "score": attempt.score,
                "completed_at": attempt.completed_at.isoformat(),
                "received_at": attempt.received_at.isoformat(),
            },
        },
        status=201 if created else 200,
    )


@csrf_exempt
def user_by_slug(request, username):
    """GET/POST /api/users/<username>/: read or update a user."""
    # The username is used as the user's slug. The implementation is
    # intentionally commented out while the update rules are finalized.
    #
    # profile = get_object_or_404(
    #     UserProfile.objects.select_related("user"), user__username=username
    # )
    # if request.method == "GET":
    #     return JsonResponse({...})
    # if request.method == "POST":
    #     payload = json.loads(request.body or "{}")
    #     ...
    #     profile.save()
    #     return JsonResponse({...})
    return JsonResponse({"detail": "Not implemented."}, status=501)


@require_GET
def leaderboard(request):
    profiles = UserProfile.objects.select_related("user").order_by("-total_score")[:10]
    return JsonResponse(
        {
            "leaderboard": [
                {
                    "user_id": profile.user_id,
                    "username": profile.user.username,
                    "avatar": profile.avatar,
                    "total_score": profile.total_score,
                }
                for profile in profiles
            ]
        }
    )
