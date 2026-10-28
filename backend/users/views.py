import json

from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError, transaction
from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.shortcuts import get_object_or_404
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from .forms import SignupForm
from .models import UserProfile


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
    return JsonResponse(
        {
            "user_id": profile.user_id,
            "username": profile.user.username,
            "avatar": profile.avatar,
            "total_score": profile.total_score,
            "completed_challenges": len(profile.scores),
            "scores": profile.scores,
        }
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
