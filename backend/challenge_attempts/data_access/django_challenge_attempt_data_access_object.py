from datetime import datetime

from django.db import transaction

from challenges.models import Challenge
from users.models import UserProfile

from ..models import ChallengeAttempt
from ..use_case.record_challenge_attempt.record_challenge_attempt_data_access_interface import (
    AttemptConflictError,
    RecordChallengeAttemptDataAccessInterface,
)
from ..use_case.record_challenge_attempt.record_challenge_attempt_output_data import (
    AttemptOutputData,
    RecordChallengeAttemptOutputData,
)


class DjangoChallengeAttemptDataAccessObject(RecordChallengeAttemptDataAccessInterface):
    def challenge_exists(self, challenge_slug: str) -> bool:
        return Challenge.objects.filter(slug=challenge_slug).exists()

    def save_attempt_and_update_score(
        self,
        *,
        user_id: int,
        challenge_slug: str,
        attempt_uuid: str,
        score: int,
        completed_at: datetime,
    ) -> RecordChallengeAttemptOutputData:
        with transaction.atomic():
            profile = (
                UserProfile.objects.select_for_update()
                .select_related("user")
                .get(user_id=user_id)
            )
            attempt, created = ChallengeAttempt.objects.get_or_create(
                submission_id=attempt_uuid,
                defaults={
                    "profile": profile,
                    "challenge_id": challenge_slug,
                    "score": score,
                    "completed_at": completed_at,
                },
            )
            if (
                attempt.profile_id != profile.pk
                or attempt.challenge_id != challenge_slug
                or attempt.score != score
                or attempt.completed_at != completed_at
            ):
                raise AttemptConflictError(
                    "This attempt ID has already been used for a different completion."
                )

            best_score = max(profile.scores.get(challenge_slug, 0), score)
            profile.add_score(challenge_slug, best_score)
            profile.save(update_fields=["scores", "total_score", "updated_at"])

        return RecordChallengeAttemptOutputData(
            user_id=profile.user_id,
            username=profile.user.username,
            avatar=profile.avatar,
            total_score=profile.total_score,
            completed_challenges=len(profile.scores),
            scores=dict(profile.scores),
            attempt=AttemptOutputData(
                id=attempt.pk,
                attempt_id=attempt.submission_id,
                challenge_slug=attempt.challenge_id,
                score=attempt.score,
                completed_at=attempt.completed_at,
                received_at=attempt.received_at,
            ),
            created=created,
        )
