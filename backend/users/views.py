import json
from math import isfinite
from uuid import UUID

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import IntegrityError, transaction
from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.utils.text import slugify
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from challenges.models import Challenge

from .forms import SignupForm
from .models import (
    AvatarChoices,
    ChallengeAttempt,
    UserProfile,
    validate_login_days,
    validate_scores,
)


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
@require_GET
def signup_groups(request):
    return JsonResponse(
        {"groups": list(Group.objects.order_by("name", "pk").values("id", "name"))}
    )


@never_cache
@require_POST
def signup(request):
    try:
        payload = _auth_payload(request)
    except ValueError as exc:
        return JsonResponse({"detail": str(exc)}, status=400)
    group_id = payload.get("group_id")
    if group_id is not None and (
        isinstance(group_id, bool) or not isinstance(group_id, int) or group_id <= 0
    ):
        return JsonResponse(
            {"errors": {"group_id": ["Group must be a positive integer ID or null."]}},
            status=400,
        )
    form = SignupForm(
        data={
            "username": payload["username"],
            "email": payload.get("email", ""),
            "group_id": group_id,
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
            if form.cleaned_data["group_id"] is not None:
                profile = user.profile
                profile.group = form.cleaned_data["group_id"]
                profile.save(update_fields=["group", "updated_at"])
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
def save_challenge_score(request, challenge_slug):
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
    challenge = Challenge.objects.filter(slug=challenge_slug).first()
    if challenge is None:
        return JsonResponse({"detail": "Challenge not found."}, status=404)

    stars = (
        int(payload["tone_correct"])
        + int(tone_time <= 10)
        + int(payload["action_correct"])
    )
    score = stars
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
                "challenge": challenge,
                "score": score,
                "completed_at": completed_at,
            },
        )
        if (
            attempt.profile_id != profile.pk
            or attempt.challenge_id != challenge.slug
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
            challenge.slug, max(profile.scores.get(challenge.slug, 0), score)
        )
        profile.save(update_fields=["scores", "total_score", "updated_at"])
    return JsonResponse(
        {
            **_profile_data(profile),
            "attempt": {
                "id": attempt.pk,
                "attempt_id": attempt.submission_id,
                "challenge_slug": attempt.challenge_id,
                "score": attempt.score,
                "completed_at": attempt.completed_at.isoformat(),
                "received_at": attempt.received_at.isoformat(),
            },
        },
        status=201 if created else 200,
    )


@require_http_methods(["GET", "POST"])
@never_cache
def user_by_slug(request, username):
    """GET/POST /api/users/<username>/: read or update a user."""
    if request.method == "POST" and not request.user.is_authenticated:
        return JsonResponse({"detail": "Authentication required."}, status=401)

    profile = get_object_or_404(
        UserProfile.objects.select_related("user"), user__username=username
    )
    if request.method == "GET":
        return JsonResponse(_user_data(profile))

    if request.user.pk != profile.user_id:
        return JsonResponse(
            {"detail": "You can only update your own profile."}, status=403
        )
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
    allowed_fields = {
        "slug",
        "challenge_scores",
        "total_score",
        "name",
        "team",
        "login_days",
        "avatar",
        "email",
    }
    if set(payload) - allowed_fields:
        return JsonResponse({"detail": "Unexpected profile fields."}, status=400)
    if payload.get("slug", username) != username:
        return JsonResponse(
            {"detail": "slug must match the user in the request URL."}, status=400
        )
    updated_scores = None
    if "challenge_scores" in payload:
        updated_scores = payload["challenge_scores"]
        try:
            validate_scores(updated_scores)
        except ValidationError as exc:
            return JsonResponse({"detail": str(exc)}, status=400)
    expected_total = (
        sum(updated_scores.values())
        if updated_scores is not None
        else profile.total_score
    )
    if "total_score" in payload:
        total_score = payload["total_score"]
        if (
            isinstance(total_score, bool)
            or not isinstance(total_score, (int, float))
            or (isinstance(total_score, float) and not isfinite(total_score))
            or total_score != expected_total
        ):
            return JsonResponse(
                {"detail": "total_score must equal the sum of challenge_scores."},
                status=400,
            )
    if "name" in payload and (
        not isinstance(payload["name"], str)
        or not payload["name"].strip()
        or len(payload["name"].strip()) > 150
    ):
        return JsonResponse(
            {"detail": "name must be a non-empty string of at most 150 characters."},
            status=400,
        )
    if "team" in payload and not isinstance(payload["team"], str):
        return JsonResponse({"detail": "team must be a string."}, status=400)
    if "login_days" in payload:
        try:
            validate_login_days(payload["login_days"])
        except ValidationError as exc:
            return JsonResponse({"detail": str(exc)}, status=400)
    if "avatar" in payload and payload["avatar"] not in AvatarChoices.values:
        return JsonResponse(
            {"detail": "avatar must be one of the supported avatar values."},
            status=400,
        )
    if "email" in payload:
        if not isinstance(payload["email"], str) or len(payload["email"]) > 254:
            return JsonResponse(
                {"detail": "email must be a string of at most 254 characters."},
                status=400,
            )
        if payload["email"]:
            try:
                validate_email(payload["email"])
            except ValidationError:
                return JsonResponse(
                    {"detail": "email must be a valid email address."}, status=400
                )

    if "team" in payload:
        team_slug = payload["team"]
        if not team_slug:
            profile.group = None
        else:
            matching_groups = [
                group
                for group in Group.objects.order_by("pk")
                if slugify(group.name) == team_slug
            ]
            if len(matching_groups) != 1:
                return JsonResponse(
                    {"detail": "team must match an existing, unique team slug."},
                    status=400,
                )
            profile.group = matching_groups[0]
    if "avatar" in payload:
        profile.avatar = payload["avatar"]
    if updated_scores is not None:
        profile.scores = updated_scores
        profile.total_score = expected_total
    if "login_days" in payload:
        profile.login_days = sorted(payload["login_days"])
    if "name" in payload:
        profile.user.first_name = payload["name"].strip()
        profile.user.last_name = ""
    if "email" in payload:
        profile.user.email = payload["email"]

    update_fields = ["updated_at"]
    profile_fields = ("group", "avatar", "login_days")
    update_fields.extend(field for field in profile_fields if field in payload)
    if updated_scores is not None:
        update_fields.extend(("scores", "total_score"))
    if "team" in payload:
        update_fields.append("group")
    with transaction.atomic():
        if "name" in payload or "email" in payload:
            user_fields = []
            if "name" in payload:
                user_fields.append("first_name")
                user_fields.append("last_name")
            if "email" in payload:
                user_fields.append("email")
            profile.user.save(update_fields=user_fields)
        profile.save(update_fields=update_fields)
    return JsonResponse(_user_data(profile))


def _user_data(profile):
    return {
        "slug": profile.user.username,
        "challenge_scores": profile.scores,
        "total_score": float(profile.total_score),
        "name": profile.user.get_full_name().strip() or profile.user.username,
        "team": slugify(profile.group.name) if profile.group else "",
        "login_days": sorted(profile.login_days),
        "avatar": profile.avatar,
        "email": profile.user.email,
    }


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
