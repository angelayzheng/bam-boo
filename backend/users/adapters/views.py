import json
from uuid import UUID

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import Group
from django.db import IntegrityError, transaction
from django.http import Http404, JsonResponse
from django.middleware.csrf import get_token
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from config.container import get_container
from users.adapters.sessionAccountGateway import DjangoSessionAccountGateway
from users.forms import SignupForm
from users.models import UserProfile


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
    """GET /api/users/auth/csrf/: return a token for subsequent POST requests."""
    return JsonResponse({"csrfToken": get_token(request)})


@never_cache
@require_GET
def signup_groups(request):
    """GET /api/users/groups/: return groups available during signup."""
    return JsonResponse(
        {"groups": list(Group.objects.order_by("name", "pk").values("id", "name"))}
    )


@never_cache
@require_POST
def signup(request):
    """POST /api/users/auth/signup/: create an account and return session data."""
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
    """POST /api/users/auth/login/: authenticate and return session data."""
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
    """POST /api/users/auth/logout/: end the current session."""
    logout(request)
    return JsonResponse({"detail": "Logged out."})


@never_cache
@require_GET
def current_user(request):
    """GET /api/users/auth/me/: return the current signed-in user's account data."""
    use_case = get_container().build_get_current_user_use_case(
        accounts=DjangoSessionAccountGateway(request),
        csrf_token=lambda: get_token(request),
    )
    use_case.controller.execute()
    return JsonResponse(
        use_case.presenter.response_body, status=use_case.presenter.status_code
    )


@require_GET
def user_profile(request, user_id):
    """GET /api/users/<id>/profile/: return public score and progress data."""
    use_case = get_container().build_view_profile_use_case()
    use_case.controller.execute(user_id=user_id)
    return _profile_response(use_case.presenter)


@never_cache
@require_POST
def save_challenge_score(request, challenge_slug):
    """POST /api/users/me/scores/<challenge_slug>/: claim a completed run and save its score."""
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
    if not isinstance(payload, dict) or set(payload) != {"attempt_id"}:
        return JsonResponse(
            {"detail": "A completed attempt_id is required."}, status=400
        )
    try:
        attempt_id = str(UUID(payload["attempt_id"]))
    except ValueError, TypeError, AttributeError:
        return JsonResponse({"detail": "attempt_id must be a valid UUID."}, status=400)

    use_case = get_container().build_record_challenge_attempt_use_case()
    use_case.controller.execute(
        user_id=request.user.pk,
        challenge_slug=challenge_slug,
        attempt_id=attempt_id,
    )
    return JsonResponse(
        use_case.presenter.response_body, status=use_case.presenter.status_code
    )


@require_http_methods(["GET", "POST"])
@never_cache
def user_by_slug(request, username):
    """GET/POST /api/users/<username>/: read a profile or update it as its owner."""
    if request.method == "GET":
        use_case = get_container().build_view_profile_use_case()
        use_case.controller.execute(username=username)
    else:
        use_case = get_container().build_update_profile_use_case()
        use_case.controller.execute(
            username=username,
            user_id=request.user.pk if request.user.is_authenticated else None,
            body=request.body,
            content_type=request.content_type,
        )
    return _profile_response(use_case.presenter)


def _profile_response(presenter):
    if presenter.status_code == 404:
        raise Http404("No UserProfile matches the given query.")
    return JsonResponse(presenter.response_body, status=presenter.status_code)


@require_GET
def leaderboard(request):
    """GET /api/users/leaderboard/: return the ten highest-scoring profiles."""
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
