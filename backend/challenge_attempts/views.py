import json

from django.http import JsonResponse
from django.utils.dateparse import parse_datetime
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST

from .data_access.django_challenge_attempt_data_access_object import (
    DjangoChallengeAttemptDataAccessObject,
)
from .interface_adapter.record_challenge_attempt.record_challenge_attempt_controller import (
    RecordChallengeAttemptController,
)
from .interface_adapter.record_challenge_attempt.record_challenge_attempt_presenter import (
    RecordChallengeAttemptPresenter,
)
from .use_case.record_challenge_attempt.record_challenge_attempt_interactor import (
    RecordChallengeAttemptInteractor,
)


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

    completed_at_raw = payload.get("completed_at")
    completed_at = None
    if isinstance(completed_at_raw, str):
        try:
            completed_at = parse_datetime(completed_at_raw)
        except TypeError, ValueError, OverflowError:
            completed_at = None

    dao = DjangoChallengeAttemptDataAccessObject()
    presenter = RecordChallengeAttemptPresenter()
    interactor = RecordChallengeAttemptInteractor(
        user_data_access_object=dao, presenter=presenter
    )
    controller = RecordChallengeAttemptController(interactor=interactor)

    controller.execute(
        user_id=request.user.pk,
        challenge_slug=challenge_slug,
        attempt_id=payload.get("attempt_id"),
        tone_correct=payload.get("tone_correct"),
        action_correct=payload.get("action_correct"),
        tone_time=payload.get("tone_time"),
        completed_at=completed_at,
    )

    return JsonResponse(presenter.response_body, status=presenter.status_code)
