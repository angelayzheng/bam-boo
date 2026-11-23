from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from challenges import models as challenge_models
from challenges.domain.ChallengePackage import ChallengePackageError
from challenges.domain.challenge import Challenge
from challenges.use_cases.ports import ChallengeRepository


def _to_domain(row: challenge_models.Challenge) -> Challenge:
    return Challenge(
        name=row.name,
        slug=row.slug,
        challenge_date=row.challenge_date,
        difficulty=row.difficulty,
        category=row.category,
        tone=row.tone,
        required_action=row.required_action,
        conversation_tree=row.conversation_tree or {},
    )


class DjangoChallengeRepository(ChallengeRepository):
    def list(self):
        return [_to_domain(row) for row in challenge_models.Challenge.objects.all()]

    def get_by_slug(self, slug: str) -> Challenge | None:
        row = challenge_models.Challenge.objects.filter(slug=slug).first()
        return None if row is None else _to_domain(row)

    def get_by_name(self, name: str) -> Challenge | None:
        row = challenge_models.Challenge.objects.filter(name=name).first()
        return None if row is None else _to_domain(row)

    def get_by_date(self, challenge_date):
        row = challenge_models.Challenge.objects.filter(
            challenge_date=challenge_date
        ).first()
        return None if row is None else _to_domain(row)

    def save(self, challenge: Challenge) -> Challenge:
        tree = (
            challenge.conversation_tree.to_dict()
            if challenge.conversation_tree is not None
            else {}
        )
        try:
            row, _ = challenge_models.Challenge.objects.update_or_create(
                slug=challenge.slug,
                defaults={
                    "name": challenge.name,
                    "challenge_date": challenge.challenge_date,
                    "difficulty": challenge.difficulty,
                    "category": challenge.category,
                    "tone": challenge.tone,
                    "required_action": challenge.required_action,
                    "conversation_tree": tree,
                },
            )
        except IntegrityError as exc:
            if transaction.get_connection().in_atomic_block:
                transaction.set_rollback(True)
            raise ChallengePackageError(
                f"Could not save challenge {challenge.slug!r}: {exc}"
            ) from exc
        except ValidationError as exc:
            raise ChallengePackageError(
                f"Could not save challenge {challenge.slug!r}: {exc}"
            ) from exc
        return _to_domain(row)
