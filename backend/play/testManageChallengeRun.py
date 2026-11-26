"""Run workflow tests with in-memory ports; no Django, database, or vectors."""

from contextlib import contextmanager
from copy import deepcopy
from dataclasses import replace
from datetime import date, datetime, timedelta, timezone
from unittest import TestCase
from uuid import UUID

from challenges.domain.challenge import Challenge
from challenges.domain.conversationNode import ConversationNode
from play.domain.run import Run
from play.useCases.manageChallengeRun.Errors import ToneAnswerUnknown, ToneUnavailable
from play.useCases.manageChallengeRun.InputData import (
    ChallengeRunInputData,
    StartChallengeRunInputData,
)
from play.useCases.manageChallengeRun.Interactor import ManageChallengeRunInteractor
from play.useCases.manageChallengeRun.OutputData import PlayFailureReason

NOW = datetime(2026, 11, 25, 15, tzinfo=timezone.utc)
RUN_ID = "12345678-1234-5678-1234-567812345678"


class InMemoryChallenges:
    def __init__(self, challenge):
        self.challenge = challenge
        self.lookups = []

    def get_by_slug(self, slug):
        self.lookups.append(slug)
        return (
            self.challenge if self.challenge and self.challenge.slug == slug else None
        )


class InMemoryRuns:
    def __init__(self):
        self.records = {}
        self.lookups = []
        self.created = []
        self.saved = []
        self.write_error = None

    def get_by_id(self, run_id, *, for_update=False):
        self.lookups.append((run_id, for_update))
        return deepcopy(self.records.get(run_id))

    def create(self, run):
        if self.write_error:
            raise self.write_error
        self.records[run.id] = deepcopy(run)
        self.created.append(deepcopy(run))
        return run

    def save(self, run):
        if self.write_error:
            raise self.write_error
        self.records[run.id] = deepcopy(run)
        self.saved.append(deepcopy(run))
        return run


class RecordingUnitOfWork:
    def __init__(self):
        self.events = []

    @contextmanager
    def atomic(self):
        self.events.append("begin")
        try:
            yield
        except Exception:
            self.events.append("rollback")
            raise
        else:
            self.events.append("commit")


class RecordingToneMatcher:
    def __init__(self):
        self.calls = []
        self.value = 0.8
        self.error = None

    def similarity(self, answer, reference_tone):
        self.calls.append((answer, reference_tone))
        if self.error:
            raise self.error
        return self.value


class RecordingAttemptRecorder:
    def __init__(self):
        self.calls = []

    def record_completed_run(self, run):
        self.calls.append(deepcopy(run))


class RecordingOutput:
    def __init__(self):
        self.successes = []
        self.failures = []

    def prepare_success_view(self, output):
        self.successes.append(output)

    def prepare_fail_view(self, failure):
        self.failures.append(failure)


class ManageChallengeRunInteractorTests(TestCase):
    def setUp(self):
        self.challenge = Challenge(
            name="Greeting",
            slug="greeting",
            challenge_date=date(2026, 11, 25),
            difficulty=1,
            category="social",
            tone="friendly",
            required_action="say hello",
            conversation_tree=ConversationNode(
                kind="question",
                text_file="q1.txt",
                audio_file="q1.mp3",
                node_key="q1",
            ),
        )
        self.challenges = InMemoryChallenges(self.challenge)
        self.runs = InMemoryRuns()
        self.unit_of_work = RecordingUnitOfWork()
        self.matcher = RecordingToneMatcher()
        self.recorder = RecordingAttemptRecorder()
        self.output = RecordingOutput()

    def interactor(self, **overrides):
        ports = dict(
            challenges=self.challenges,
            runs=self.runs,
            attempt_recorder=self.recorder,
            unit_of_work=self.unit_of_work,
            tone_matcher=self.matcher,
            presenter=self.output,
            now=lambda: NOW,
        )
        ports.update(overrides)
        return ManageChallengeRunInteractor(**ports)

    def store_run(self, **overrides):
        values = dict(
            id=RUN_ID,
            challenge_slug="greeting",
            current_node="q1",
            created_at=NOW - timedelta(seconds=13.25),
            user_id=7,
        )
        values.update(overrides)
        run = Run(**values)
        self.runs.records[run.id] = deepcopy(run)
        return run

    def run_input(self, **overrides):
        values = dict(run_id=RUN_ID, user_id=7, payload={"answer": "warm"})
        values.update(overrides)
        return ChallengeRunInputData(**values)

    def assert_failure(self, reason, message):
        self.assertEqual(self.output.successes, [])
        self.assertEqual(len(self.output.failures), 1)
        failure = self.output.failures[0]
        self.assertEqual(failure.reason, reason)
        self.assertEqual(failure.message, message)
        self.assertEqual(self.runs.created, [])
        self.assertEqual(self.runs.saved, [])
        self.assertEqual(self.recorder.calls, [])

    def test_start_creates_a_fresh_guest_or_owned_run_at_the_opening_node(self):
        for user_id in (None, 7):
            with self.subTest(user_id=user_id):
                self.setUp()
                self.interactor().start_challenge(
                    StartChallengeRunInputData("greeting", user_id, {})
                )

                self.assertEqual(self.output.failures, [])
                self.assertEqual(len(self.output.successes), 1)
                output = self.output.successes[0]
                self.assertEqual(output.status_code, 201)
                self.assertEqual(output.challenge, self.challenge)
                run = output.run
                self.assertEqual(UUID(run.id).version, 4)
                self.assertEqual(run.challenge_slug, "greeting")
                self.assertEqual(run.user_id, user_id)
                self.assertEqual(run.created_at, NOW)
                self.assertEqual(run.current_node, "q1")
                self.assertEqual(run.stage, "tone")
                self.assertEqual(run.conversation, [])
                self.assertIsNone(run.tone_correct)
                self.assertIsNone(run.score)
                self.assertEqual(self.runs.records, {run.id: run})
                self.assertEqual(self.runs.created, [run])
                self.assertEqual(self.unit_of_work.events, ["begin", "commit"])
                self.assertEqual(self.matcher.calls, [])
                self.assertEqual(self.recorder.calls, [])

    def test_start_rejects_client_supplied_state_without_accessing_repositories(self):
        self.interactor().start_challenge(
            StartChallengeRunInputData("greeting", 7, {"score": 3})
        )

        self.assert_failure(
            PlayFailureReason.INVALID_INPUT, "Expected an empty JSON object."
        )
        self.assertEqual(self.challenges.lookups, [])
        self.assertEqual(self.unit_of_work.events, [])

    def test_start_reports_a_missing_challenge_without_creating_a_run(self):
        self.interactor().start_challenge(StartChallengeRunInputData("missing", 7, {}))

        self.assert_failure(
            PlayFailureReason.CHALLENGE_NOT_FOUND, "Challenge not found."
        )
        self.assertEqual(self.unit_of_work.events, ["begin", "rollback"])

    def test_start_requires_a_tree_with_an_opening_node_key(self):
        for tree in (None, replace(self.challenge.conversation_tree, node_key=None)):
            with self.subTest(tree=tree):
                self.setUp()
                self.challenges.challenge = replace(
                    self.challenge, conversation_tree=tree
                )
                self.interactor().start_challenge(
                    StartChallengeRunInputData("greeting", None, {})
                )

                self.assert_failure(
                    PlayFailureReason.CHALLENGE_UNAVAILABLE,
                    "Challenge is not available to play.",
                )
                self.assertEqual(self.unit_of_work.events, ["begin", "rollback"])

    def test_start_reports_repository_validation_errors_through_the_output_boundary(
        self,
    ):
        self.runs.write_error = ValueError("Run could not be created.")

        self.interactor().start_challenge(StartChallengeRunInputData("greeting", 7, {}))

        self.assert_failure(
            PlayFailureReason.INVALID_INPUT, "Run could not be created."
        )
        self.assertEqual(self.unit_of_work.events, ["begin", "rollback"])

    def test_resume_preserves_progress_in_every_stage_without_writing_or_grading(self):
        for stage in ("tone", "conversation", "action", "completed"):
            with self.subTest(stage=stage):
                self.setUp()
                run = self.store_run(stage=stage)
                if stage != "tone":
                    run.record_tone(0.8, True, 13.25, "q1")
                    run.stage = stage
                if stage == "completed":
                    run.complete(True, 2, NOW)
                self.runs.records[run.id] = deepcopy(run)

                self.interactor().get_run(self.run_input(payload={}))

                self.assertEqual(self.output.failures, [])
                self.assertEqual(len(self.output.successes), 1)
                output = self.output.successes[0]
                self.assertEqual(output.run, run)
                self.assertEqual(output.challenge, self.challenge)
                self.assertEqual(output.status_code, 200)
                self.assertEqual(self.runs.records[RUN_ID], run)
                self.assertEqual(self.runs.lookups, [(RUN_ID, False)])
                self.assertEqual(self.runs.created, [])
                self.assertEqual(self.runs.saved, [])
                self.assertEqual(self.unit_of_work.events, [])
                self.assertEqual(self.matcher.calls, [])
                self.assertEqual(self.recorder.calls, [])

    def test_resume_allows_guest_runs_for_anonymous_and_signed_in_callers(self):
        run = self.store_run(user_id=None)
        for user_id in (None, 7):
            with self.subTest(user_id=user_id):
                self.output.successes.clear()
                self.interactor().get_run(self.run_input(user_id=user_id, payload={}))
                self.assertEqual(
                    [output.run for output in self.output.successes], [run]
                )
                self.assertEqual(self.output.failures, [])

    def test_resume_and_tone_reject_missing_runs_before_looking_up_challenges(self):
        for method in ("get_run", "submit_tone"):
            with self.subTest(method=method):
                self.setUp()
                getattr(self.interactor(), method)(self.run_input())

                self.assert_failure(
                    PlayFailureReason.RUN_NOT_FOUND, "Attempt not found."
                )
                self.assertEqual(self.challenges.lookups, [])
                self.assertEqual(self.matcher.calls, [])

    def test_resume_and_tone_reject_owned_runs_for_other_or_anonymous_callers(self):
        for method in ("get_run", "submit_tone"):
            for user_id in (None, 8):
                with self.subTest(method=method, user_id=user_id):
                    self.setUp()
                    original = self.store_run()
                    getattr(self.interactor(), method)(self.run_input(user_id=user_id))

                    self.assert_failure(
                        PlayFailureReason.RUN_FORBIDDEN,
                        "This attempt belongs to another account.",
                    )
                    self.assertEqual(self.runs.records[RUN_ID], original)
                    self.assertEqual(self.challenges.lookups, [])
                    self.assertEqual(self.matcher.calls, [])

    def test_resume_and_tone_report_deleted_challenges_without_changing_the_run(self):
        for method in ("get_run", "submit_tone"):
            with self.subTest(method=method):
                self.setUp()
                original = self.store_run(challenge_slug="deleted")
                getattr(self.interactor(), method)(self.run_input())

                self.assert_failure(
                    PlayFailureReason.CHALLENGE_NOT_FOUND, "Challenge not found."
                )
                self.assertEqual(self.runs.records[RUN_ID], original)
                self.assertEqual(self.matcher.calls, [])

    def test_tone_uses_the_private_reference_and_server_clock_and_persists_feedback(
        self,
    ):
        for similarity, correct in (
            (0.65, True),
            (0.6499, False),
            (-0.4, False),
            (1.0, True),
        ):
            for user_id in (None, 7):
                with self.subTest(similarity=similarity, user_id=user_id):
                    self.setUp()
                    self.store_run(user_id=user_id)
                    self.matcher.value = similarity
                    self.interactor().submit_tone(self.run_input(user_id=user_id))

                    self.assertEqual(self.output.failures, [])
                    self.assertEqual(len(self.output.successes), 1)
                    output = self.output.successes[0]
                    run = output.run
                    self.assertEqual(output.status_code, 200)
                    self.assertEqual(self.matcher.calls, [("warm", "friendly")])
                    self.assertEqual(run.tone_similarity, similarity)
                    self.assertIs(run.tone_correct, correct)
                    self.assertEqual(run.tone_time, 13.25)
                    self.assertEqual(run.stage, "conversation")
                    self.assertEqual(run.current_node, "q1")
                    self.assertEqual(run.conversation, ["q1"])
                    self.assertIsNone(run.score)
                    self.assertEqual(self.runs.records[RUN_ID], run)
                    self.assertEqual(self.runs.saved, [run])
                    self.assertEqual(self.runs.lookups, [(RUN_ID, True)])
                    self.assertEqual(self.unit_of_work.events, ["begin", "commit"])
                    self.assertEqual(self.recorder.calls, [])

    def test_tone_clamps_negative_elapsed_time_to_zero(self):
        self.store_run(created_at=NOW + timedelta(seconds=1))

        self.interactor().submit_tone(self.run_input())

        self.assertEqual(self.output.successes[0].run.tone_time, 0)
        self.assertEqual(self.runs.records[RUN_ID].tone_time, 0)

    def test_tone_accepts_the_maximum_answer_length(self):
        self.store_run()
        answer = "x" * 200

        self.interactor().submit_tone(self.run_input(payload={"answer": answer}))

        self.assertEqual(self.matcher.calls, [(answer, "friendly")])
        self.assertEqual(len(self.output.successes), 1)
        self.assertEqual(self.output.failures, [])

    def test_tone_rejects_malformed_or_oversized_answers_without_grading_or_saving(
        self,
    ):
        for payload in (
            {},
            {"answer": None},
            {"answer": 5},
            {"answer": []},
            {"answer": "warm", "tone_time": 0},
            {"answer": "x" * 201},
        ):
            with self.subTest(payload=payload):
                self.setUp()
                original = self.store_run()
                self.interactor().submit_tone(self.run_input(payload=payload))

                message = (
                    "answer must be at most 200 characters."
                    if payload == {"answer": "x" * 201}
                    else "answer must be a string."
                )
                self.assert_failure(PlayFailureReason.INVALID_INPUT, message)
                self.assertEqual(self.matcher.calls, [])
                self.assertEqual(self.runs.records[RUN_ID], original)
                self.assertEqual(self.unit_of_work.events, ["begin", "rollback"])

    def test_tone_rejects_replays_in_later_stages_before_grading(self):
        for stage in ("conversation", "action", "completed"):
            with self.subTest(stage=stage):
                self.setUp()
                original = self.store_run(stage=stage)
                self.interactor().submit_tone(self.run_input())

                self.assert_failure(
                    PlayFailureReason.INVALID_STAGE, "Invalid attempt stage transition."
                )
                self.assertEqual(self.matcher.calls, [])
                self.assertEqual(self.runs.records[RUN_ID], original)
                self.assertEqual(self.unit_of_work.events, ["begin", "rollback"])

    def test_tone_matcher_failures_leave_the_run_retryable(self):
        for error, reason in (
            (
                ToneAnswerUnknown("Unknown tone answer."),
                PlayFailureReason.UNKNOWN_TONE_ANSWER,
            ),
            (
                ToneUnavailable("Vectors unavailable."),
                PlayFailureReason.TONE_UNAVAILABLE,
            ),
        ):
            with self.subTest(reason=reason):
                self.setUp()
                original = self.store_run()
                self.matcher.error = error
                self.interactor().submit_tone(self.run_input())

                self.assert_failure(reason, str(error))
                self.assertEqual(self.runs.records[RUN_ID], original)
                self.assertEqual(self.unit_of_work.events, ["begin", "rollback"])

                self.matcher.error = None
                self.output.failures.clear()
                self.interactor().submit_tone(self.run_input())
                self.assertEqual(len(self.output.successes), 1)
                self.assertEqual(self.runs.records[RUN_ID].stage, "conversation")

    def test_tone_without_a_matcher_reports_service_unavailability(self):
        original = self.store_run()

        self.interactor(tone_matcher=None).submit_tone(self.run_input())

        self.assert_failure(
            PlayFailureReason.TONE_UNAVAILABLE, "Tone vectors are unavailable."
        )
        self.assertEqual(self.runs.records[RUN_ID], original)
        self.assertEqual(self.unit_of_work.events, ["begin", "rollback"])

    def test_tone_rejects_non_finite_or_non_numeric_similarity_without_saving(self):
        for value in (float("nan"), float("inf"), float("-inf"), True, "0.8", None):
            with self.subTest(value=value):
                self.setUp()
                original = self.store_run()
                self.matcher.value = value
                self.interactor().submit_tone(self.run_input())

                self.assert_failure(
                    PlayFailureReason.INVALID_INPUT,
                    "Tone similarity must be a finite number.",
                )
                self.assertEqual(self.runs.records[RUN_ID], original)
                self.assertEqual(self.unit_of_work.events, ["begin", "rollback"])

    def test_tone_save_validation_failure_does_not_present_success(self):
        original = self.store_run()
        self.runs.write_error = ValueError("Run could not be saved.")

        self.interactor().submit_tone(self.run_input())

        self.assert_failure(PlayFailureReason.INVALID_INPUT, "Run could not be saved.")
        self.assertEqual(self.runs.records[RUN_ID], original)
        self.assertEqual(self.unit_of_work.events, ["begin", "rollback"])
