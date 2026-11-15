import json

from django.http import JsonResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST

from .use_cases import (
    AttemptConflict,
    ChallengeNotFound,
    InvalidAttemptData,
    RecordChallengeAttempt,
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
    except (ValueError, UnicodeDecodeError):
        return JsonResponse({"detail": "Expected a valid JSON object."}, status=400)

    try:
        profile, attempt, created = RecordChallengeAttempt().execute(
            user=request.user,
            challenge_slug=challenge_slug,
            payload=payload,
        )
    except InvalidAttemptData as exc:
        return JsonResponse({"detail": str(exc)}, status=400)
    except ChallengeNotFound as exc:
        return JsonResponse({"detail": str(exc)}, status=404)
    except AttemptConflict as exc:
        return JsonResponse({"detail": str(exc)}, status=409)

    return JsonResponse(
        {
            "user_id": profile.user_id,
            "username": profile.user.username,
            "avatar": profile.avatar,
            "total_score": profile.total_score,
            "completed_challenges": len(profile.scores),
            "scores": profile.scores,
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
