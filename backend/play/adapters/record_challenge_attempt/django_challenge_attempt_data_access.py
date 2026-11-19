from django.db import transaction

from challenges.models import Challenge
from play.domain.attempt import Attempt
from play.use_cases.record_challenge_attempt.record_challenge_attempt_data_access_interface import (
    AttemptConflictError,
    RecordChallengeAttemptDataAccessInterface,
    RecordedChallengeAttempt,
)
from users.domain.profile import Profile
from users.models import ChallengeAttempt, UserProfile


class DjangoChallengeAttemptDataAccess(RecordChallengeAttemptDataAccessInterface):
    def challenge_exists(self, challenge_slug: str) -> bool:
        return Challenge.objects.filter(slug=challenge_slug).exists()

    def record(self, attempt: Attempt) -> RecordedChallengeAttempt:
        with transaction.atomic():
            profile = (
                UserProfile.objects.select_for_update()
                .select_related("user")
                .get(user_id=attempt.profile_id)
            )
            stored, created = ChallengeAttempt.objects.get_or_create(
                submission_id=attempt.submission_id,
                defaults={
                    "profile": profile,
                    "challenge_id": attempt.challenge_slug,
                    "score": attempt.score,
                    "completed_at": attempt.completed_at,
                },
            )
            stored_attempt = Attempt(
                submission_id=stored.submission_id,
                profile_id=stored.profile_id,
                challenge_slug=stored.challenge_id,
                score=stored.score,
                completed_at=stored.completed_at,
                received_at=stored.received_at,
                record_id=stored.pk,
            )
            if not stored_attempt.matches_completion(
                attempt.profile_id,
                attempt.challenge_slug,
                attempt.score,
                attempt.completed_at,
            ):
                raise AttemptConflictError(
                    "This attempt ID has already been used for a different completion."
                )

            domain_profile = Profile(
                user_id=profile.user_id,
                username=profile.user.username,
                avatar=profile.avatar,
                scores=dict(profile.scores),
            )
            domain_profile.add_score(attempt.challenge_slug, attempt.score)
            profile.scores = domain_profile.scores
            profile.total_score = domain_profile.total_score
            profile.save(update_fields=["scores", "total_score", "updated_at"])

        return RecordedChallengeAttempt(
            attempt=stored_attempt,
            profile=domain_profile,
            created=created,
        )
