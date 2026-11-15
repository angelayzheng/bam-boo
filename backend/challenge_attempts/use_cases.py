import json
from math import isfinite
from uuid import UUID

from django.db import transaction
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from challenges.models import Challenge
from users.models import UserProfile

from .models import ChallengeAttempt


class InvalidAttemptData(ValueError):
    pass


class ChallengeNotFound(ValueError):
    pass


class AttemptConflict(ValueError):
    pass


class RecordChallengeAttempt:
    def execute(self, *, user, challenge_slug, payload):
        if not isinstance(payload, dict):
            raise InvalidAttemptData("Expected a JSON object.")

        tone_correct = payload.get("tone_correct")
        action_correct = payload.get("action_correct")
        if not isinstance(tone_correct, bool) or not isinstance(action_correct, bool):
            raise InvalidAttemptData(
                "tone_correct and action_correct must be booleans."
            )

        tone_time = payload.get("tone_time")
        if (
            isinstance(tone_time, bool)
            or not isinstance(tone_time, (int, float))
            or (isinstance(tone_time, float) and not isfinite(tone_time))
            or tone_time < 0
        ):
            raise InvalidAttemptData(
                "tone_time must be a finite, non-negative number of seconds."
            )

        try:
            attempt_id = payload.get("attempt_id")
            if not isinstance(attempt_id, str):
                raise ValueError
            attempt_uuid = str(UUID(attempt_id))
            completed_at_raw = payload.get("completed_at")
            if not isinstance(completed_at_raw, str):
                raise ValueError
            completed_at = parse_datetime(completed_at_raw)
            if completed_at is None or timezone.is_naive(completed_at):
                raise ValueError
        except (TypeError, ValueError, OverflowError) as exc:
            raise InvalidAttemptData(
                "A valid attempt_id UUID and timezone-aware completed_at timestamp are required."
            ) from exc

        challenge = Challenge.objects.filter(slug=challenge_slug).first()
        if challenge is None:
            raise ChallengeNotFound("Challenge not found.")

        score = int(tone_correct) + int(tone_time <= 10) + int(action_correct)
        with transaction.atomic():
            profile = (
                UserProfile.objects.select_for_update()
                .select_related("user")
                .get(user=user)
            )
            attempt, created = ChallengeAttempt.objects.get_or_create(
                submission_id=attempt_uuid,
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
                raise AttemptConflict(
                    "This attempt ID has already been used for a different completion."
                )
            profile.add_score(challenge.slug, max(profile.scores.get(challenge.slug, 0), score))
            profile.save(update_fields=["scores", "total_score", "updated_at"])

        return profile, attempt, created
