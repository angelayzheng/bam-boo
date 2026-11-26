from dataclasses import asdict
from datetime import date
from unittest import TestCase

from challenges.adapters.getChallenge.Controller import GetChallengeController
from challenges.adapters.getChallenge.Presenter import GetChallengePresenter
from challenges.domain.challenge import Challenge
from challenges.useCases.getChallenge.InputData import GetChallengeInputData
from challenges.useCases.getChallenge.Interactor import GetChallengeInteractor


class InMemoryChallenges:
    def __init__(self, challenge):
        self.challenge = challenge
        self.lookups = []

    def get_by_slug(self, slug):
        self.lookups.append(slug)
        return self.challenge if slug == self.challenge.slug else None


class RecordingOutput:
    def __init__(self):
        self.successes = []
        self.failures = []

    def prepare_success_view(self, output):
        self.successes.append(output)

    def prepare_fail_view(self, failure):
        self.failures.append(failure)


class GetChallengeInteractorTests(TestCase):
    def setUp(self):
        # Public metadata remains available even without a playable conversation.
        self.challenge = Challenge(
            name="Greeting",
            slug="greeting",
            challenge_date=date(2026, 11, 25),
            difficulty=2,
            category="social",
            tone="private tone",
            required_action="private action",
        )
        self.challenges = InMemoryChallenges(self.challenge)
        self.output = RecordingOutput()
        self.interactor = GetChallengeInteractor(
            challenges=self.challenges, presenter=self.output
        )

    def test_returns_only_public_metadata_through_the_output_boundary(self):
        self.interactor.execute(GetChallengeInputData(slug="greeting"))

        self.assertEqual(self.challenges.lookups, ["greeting"])
        self.assertEqual(self.output.failures, [])
        self.assertEqual(len(self.output.successes), 1)
        self.assertEqual(
            asdict(self.output.successes[0]),
            {
                "name": "Greeting",
                "slug": "greeting",
                "challenge_date": date(2026, 11, 25),
                "difficulty": 2,
                "category": "social",
            },
        )

    def test_missing_slug_reports_a_semantic_failure_without_success(self):
        self.interactor.execute(GetChallengeInputData(slug="missing"))

        self.assertEqual(self.challenges.lookups, ["missing"])
        self.assertEqual(self.output.successes, [])
        self.assertEqual(len(self.output.failures), 1)
        self.assertEqual(self.output.failures[0].message, "Challenge not found.")
        self.assertFalse(hasattr(self.output.failures[0], "status_code"))

    def test_controller_and_presenter_preserve_the_json_contract_and_clear_old_failures(
        self,
    ):
        presenter = GetChallengePresenter()
        controller = GetChallengeController(
            GetChallengeInteractor(challenges=self.challenges, presenter=presenter)
        )

        controller.execute("missing")
        self.assertEqual(presenter.status_code, 404)
        self.assertEqual(presenter.response_body, {"detail": "Challenge not found."})

        controller.execute("greeting")
        self.assertEqual(presenter.status_code, 200)
        self.assertEqual(
            presenter.response_body,
            {
                "name": "Greeting",
                "slug": "greeting",
                "challenge_date": "2026-11-25",
                "difficulty": 2,
                "category": "social",
            },
        )

        controller.execute("missing")
        self.assertEqual(presenter.status_code, 404)
        self.assertEqual(presenter.response_body, {"detail": "Challenge not found."})
