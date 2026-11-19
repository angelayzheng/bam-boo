import json

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import Group
from django.db import IntegrityError, transaction
from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_POST

from users.forms import SignupForm


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
