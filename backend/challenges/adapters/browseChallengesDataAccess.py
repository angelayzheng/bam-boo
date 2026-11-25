"""Django ORM implementation of the browse-challenges data access interface.

Reads the challenges in a month and a user's scores from the database. Lives in
adapters/ because it is the only place allowed to import Django models.
"""

from challenges import models as challenge_models
from challenges.use_cases.browseChallenges.DataAccessInterface import (
    BrowseChallengesDataAccessInterface,
    ChallengeRecord,
)
from users.models import UserProfile


class DjangoBrowseChallengesDataAccess(BrowseChallengesDataAccessInterface):
    def challenges_in_month(self, year, month):
        rows = challenge_models.Challenge.objects.filter(
            challenge_date__year=year, challenge_date__month=month
        )
        return [
            ChallengeRecord(
                id=row.id,
                slug=row.slug,
                name=row.name,
                difficulty=row.difficulty,
                category=row.category,
                challenge_date=row.challenge_date,
            )
            for row in rows
        ]

    def best_scores(self, user_id, challenge_ids):
        profile = UserProfile.objects.filter(user_id=user_id).first()
        if profile is None or not challenge_ids:
            return {}
        slugs_by_id = dict(
            challenge_models.Challenge.objects.filter(id__in=challenge_ids).values_list(
                "id", "slug"
            )
        )
        return {
            challenge_id: profile.scores[slug]
            for challenge_id, slug in slugs_by_id.items()
            if slug in profile.scores
        }
