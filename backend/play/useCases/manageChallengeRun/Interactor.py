import re
from datetime import datetime, timezone
from typing import NoReturn
from uuid import uuid4

from challenges.domain.conversationNode import ConversationNode
from challenges.useCases.ports import ChallengeRepository
from play.domain.answerMatching import AnswerMatching
from play.domain.run import Run
from play.domain.starRules import StarRules
from play.useCases.ports import (
    AttemptRecordingError,
    CompletedRunRecorder,
    RunRepository,
    ToneMatcher,
    UnitOfWork,
)
from .Errors import ToneAnswerUnknown, ToneUnavailable
from .InputBoundary import ManageChallengeRunInputBoundary
from .InputData import ChallengeRunInputData, StartChallengeRunInputData
from .OutputBoundary import ManageChallengeRunOutputBoundary
from .OutputData import PlayFailureData, PlayFailureReason, PlaySuccessData

MAX_TONE_ANSWER_LENGTH = 200


class _PlayFailure(Exception):
    def __init__(self, reason: PlayFailureReason, message: str):
        super().__init__(message)
        self.failure = PlayFailureData(reason=reason, message=message)


class ManageChallengeRunInteractor(ManageChallengeRunInputBoundary):
    """Owns the challenge-run workflow and its persistence transactions."""

    def __init__(
        self,
        *,
        challenges: ChallengeRepository,
        runs: RunRepository,
        attempt_recorder: CompletedRunRecorder,
        unit_of_work: UnitOfWork,
        tone_matcher: ToneMatcher | None,
        presenter: ManageChallengeRunOutputBoundary,
        star_rules: StarRules | None = None,
        now=None,
    ):
        self._challenges = challenges
        self._runs = runs
        self._attempt_recorder = attempt_recorder
        self._unit_of_work = unit_of_work
        self._tone_matcher = tone_matcher
        self._presenter = presenter
        self._star_rules = star_rules or StarRules()
        self._now = now or (lambda: datetime.now(timezone.utc))

    def reject_input(self, message: str) -> None:
        self._fail(PlayFailureReason.INVALID_INPUT, message)

    def start_challenge(self, input_data: StartChallengeRunInputData) -> None:
        try:
            if input_data.payload:
                self._reject("Expected an empty JSON object.")
            with self._unit_of_work.atomic():
                challenge = self._challenges.get_by_slug(input_data.challenge_slug)
                if challenge is None:
                    self._reject(
                        "Challenge not found.", PlayFailureReason.CHALLENGE_NOT_FOUND
                    )
                root = challenge.conversation_tree
                if root is None or not root.node_key:
                    self._reject(
                        "Challenge is not available to play.",
                        PlayFailureReason.CHALLENGE_UNAVAILABLE,
                    )
                run = self._runs.create(
                    Run(
                        id=str(uuid4()),
                        challenge_slug=challenge.slug,
                        user_id=input_data.user_id,
                        current_node=root.node_key,
                        created_at=self._now(),
                    )
                )
            self._success(run, challenge, status_code=201)
        except _PlayFailure as exc:
            self._presenter.prepare_fail_view(exc.failure)
        except ValueError as exc:
            self._fail(PlayFailureReason.INVALID_INPUT, str(exc))

    def get_run(self, input_data: ChallengeRunInputData) -> None:
        try:
            run = self._get_run(input_data.run_id, input_data.user_id)
            challenge = self._get_challenge(run.challenge_slug)
            self._success(run, challenge)
        except _PlayFailure as exc:
            self._presenter.prepare_fail_view(exc.failure)

    def submit_tone(self, input_data: ChallengeRunInputData) -> None:
        payload = input_data.payload

        def transition(run, challenge):
            if set(payload) != {"answer"} or not isinstance(payload["answer"], str):
                self._reject("answer must be a string.")
            if len(payload["answer"]) > MAX_TONE_ANSWER_LENGTH:
                self._reject(
                    f"answer must be at most {MAX_TONE_ANSWER_LENGTH} characters."
                )
            if self._tone_matcher is None:
                raise ToneUnavailable("Tone vectors are unavailable.")
            similarity = self._tone_matcher.similarity(
                payload["answer"], challenge.tone
            )
            elapsed = max(0.0, (self._now() - run.created_at).total_seconds())
            root = challenge.conversation_tree
            run.record_tone(
                similarity,
                AnswerMatching.tone_is_correct(similarity),
                elapsed,
                root.node_key,
            )

        self._transition(
            input_data.run_id, input_data.user_id, "tone", payload, transition
        )

    def choose_response(self, input_data: ChallengeRunInputData) -> None:
        payload = input_data.payload

        def transition(run, challenge):
            if set(payload) != {"choice_id"} or not isinstance(
                payload["choice_id"], str
            ):
                self._reject("choice_id must be a string.")
            nodes = _node_map(challenge.conversation_tree)
            current = nodes.get(run.current_node)
            choices = (
                [node for node in current.children if node.kind == "response"]
                if current is not None
                else []
            )
            choice_id = payload["choice_id"]
            if not re.fullmatch(r"\d+", choice_id) or int(choice_id) >= len(choices):
                self._reject("The selected choice is unavailable.")
            response = choices[int(choice_id)]
            followups = [node for node in response.children if node.kind == "question"]
            run.choose_response(response, followups[0] if followups else None)

        self._transition(
            input_data.run_id,
            input_data.user_id,
            "conversation",
            payload,
            transition,
        )

    def continue_conversation(self, input_data: ChallengeRunInputData) -> None:
        payload = input_data.payload

        def transition(run, challenge):
            if payload:
                self._reject("Expected an empty JSON object.")
            nodes = _node_map(challenge.conversation_tree)
            current = nodes.get(run.current_node)
            if current is None:
                self._reject("The current conversation turn is unavailable.")
            if any(node.kind == "response" for node in current.children):
                self._reject("Available responses must be selected first.")
            run.continue_conversation()

        self._transition(
            input_data.run_id,
            input_data.user_id,
            "conversation",
            payload,
            transition,
        )

    def submit_action(self, input_data: ChallengeRunInputData) -> None:
        payload = input_data.payload

        def transition(run, challenge):
            if set(payload) != {"answer"} or not isinstance(payload["answer"], str):
                self._reject("answer must be a string.")
            action_correct = AnswerMatching.action_is_correct(
                challenge.required_action, payload["answer"]
            )
            score = self._star_rules.score(
                run.tone_correct, run.tone_time, action_correct
            )
            run.complete(action_correct, score, self._now())

        self._transition(
            input_data.run_id, input_data.user_id, "action", payload, transition
        )

    def _transition(self, run_id, user_id, expected_stage, payload, transition):
        try:
            with self._unit_of_work.atomic():
                run = self._get_run(run_id, user_id, for_update=True)
                if run.stage != expected_stage:
                    self._reject(
                        "Invalid attempt stage transition.",
                        PlayFailureReason.INVALID_STAGE,
                    )
                challenge = self._get_challenge(run.challenge_slug)
                transition(run, challenge)
                self._runs.save(run)
                if run.stage == "completed" and run.user_id is not None:
                    self._attempt_recorder.record_completed_run(run)
            self._success(run, challenge)
        except _PlayFailure as exc:
            self._presenter.prepare_fail_view(exc.failure)
        except AttemptRecordingError as exc:
            reason = (
                PlayFailureReason.PROFILE_NOT_FOUND
                if exc.reason == "profile_not_found"
                else PlayFailureReason.ATTEMPT_CONFLICT
            )
            self._fail(reason, exc.message)
        except ToneAnswerUnknown as exc:
            self._fail(PlayFailureReason.UNKNOWN_TONE_ANSWER, str(exc))
        except ToneUnavailable as exc:
            self._fail(PlayFailureReason.TONE_UNAVAILABLE, str(exc))
        except ValueError as exc:
            self._fail(PlayFailureReason.INVALID_INPUT, str(exc))

    def _get_run(self, run_id, user_id, *, for_update=False):
        run = self._runs.get_by_id(run_id, for_update=for_update)
        if run is None:
            self._reject("Attempt not found.", PlayFailureReason.RUN_NOT_FOUND)
        if run.user_id is not None and run.user_id != user_id:
            self._reject(
                "This attempt belongs to another account.",
                PlayFailureReason.RUN_FORBIDDEN,
            )
        return run

    def _get_challenge(self, slug):
        challenge = self._challenges.get_by_slug(slug)
        if challenge is None:
            self._reject("Challenge not found.", PlayFailureReason.CHALLENGE_NOT_FOUND)
        return challenge

    def _success(self, run, challenge, *, status_code=200):
        self._presenter.prepare_success_view(
            PlaySuccessData(run=run, challenge=challenge, status_code=status_code)
        )

    def _fail(self, reason, message):
        self._presenter.prepare_fail_view(PlayFailureData(reason, message))

    @staticmethod
    def _reject(message, reason=PlayFailureReason.INVALID_INPUT) -> NoReturn:
        raise _PlayFailure(reason, message)


def _node_map(root: ConversationNode | None):
    result = {}

    def visit(node):
        if node.node_key is not None:
            result[node.node_key] = node
        for child in node.children:
            visit(child)

    if root is not None:
        visit(root)
    return result
