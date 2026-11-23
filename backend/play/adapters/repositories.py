from play.domain.attempt import Attempt
from play.domain.Run import Run
from play.models import ChallengeRun
from play.use_cases.ports import AttemptRepository, RunRepository
from users.models import ChallengeAttempt


def _to_domain(row: ChallengeAttempt) -> Attempt:
    return Attempt(
        submission_id=row.submission_id,
        profile_id=row.profile_id,
        challenge_slug=row.challenge_id,
        score=row.score,
        completed_at=row.completed_at,
        received_at=row.received_at,
        record_id=row.pk,
    )


class DjangoAttemptRepository(AttemptRepository):
    def get_by_submission_id(self, submission_id: str) -> Attempt | None:
        row = ChallengeAttempt.objects.filter(submission_id=submission_id).first()
        return None if row is None else _to_domain(row)

    def save(self, attempt: Attempt) -> Attempt:
        row = ChallengeAttempt.objects.create(
            submission_id=attempt.submission_id,
            profile_id=attempt.profile_id,
            challenge_id=attempt.challenge_slug,
            score=attempt.score,
            completed_at=attempt.completed_at,
        )
        return _to_domain(row)

    def get_or_create(self, attempt: Attempt) -> tuple[Attempt, bool]:
        row, created = ChallengeAttempt.objects.get_or_create(
            submission_id=attempt.submission_id,
            defaults={
                "profile_id": attempt.profile_id,
                "challenge_id": attempt.challenge_slug,
                "score": attempt.score,
                "completed_at": attempt.completed_at,
            },
        )
        return _to_domain(row), created

    def list_for_profile(self, profile_id: int) -> list[Attempt]:
        return [
            _to_domain(row)
            for row in ChallengeAttempt.objects.filter(profile_id=profile_id)
        ]


def _run_to_domain(row: ChallengeRun) -> Run:
    return Run(
        id=str(row.pk),
        challenge_slug=row.challenge_id,
        user_id=row.user_id,
        stage=row.stage,
        conversation=list(row.conversation),
        current_node=row.current_node,
        tone_correct=row.tone_correct,
        tone_time=row.tone_time,
        tone_similarity=row.tone_similarity,
        action_correct=row.action_correct,
        score=row.score,
        completed_at=row.completed_at,
        created_at=row.created_at,
    )


class DjangoRunRepository(RunRepository):
    def get_by_id(self, run_id: str, *, for_update: bool = False) -> Run | None:
        query = ChallengeRun.objects.all()
        if for_update:
            query = query.select_for_update()
        row = query.filter(pk=run_id).first()
        return None if row is None else _run_to_domain(row)

    def create(self, run: Run) -> Run:
        row = ChallengeRun.objects.create(
            pk=run.id,
            challenge_id=run.challenge_slug,
            user_id=run.user_id,
            stage=run.stage,
            conversation=run.conversation,
            current_node=run.current_node,
            tone_correct=run.tone_correct,
            tone_time=run.tone_time,
            tone_similarity=run.tone_similarity,
            action_correct=run.action_correct,
            score=run.score,
            completed_at=run.completed_at,
        )
        return _run_to_domain(row)

    def save(self, run: Run) -> Run:
        row = ChallengeRun.objects.get(pk=run.id)
        row.stage = run.stage
        row.conversation = list(run.conversation)
        row.current_node = run.current_node
        row.tone_correct = run.tone_correct
        row.tone_time = run.tone_time
        row.tone_similarity = run.tone_similarity
        row.action_correct = run.action_correct
        row.score = run.score
        row.completed_at = run.completed_at
        row.user_id = run.user_id
        row.save(
            update_fields=[
                "stage",
                "conversation",
                "current_node",
                "tone_correct",
                "tone_time",
                "tone_similarity",
                "action_correct",
                "score",
                "completed_at",
                "user",
            ]
        )
        return _run_to_domain(row)
