from dataclasses import dataclass
from datetime import date

from django.test import SimpleTestCase

from challenges.adapters.validateChallenges.Controller import (
    ValidateChallengesController,
)
from challenges.adapters.validateChallenges.Presenter import (
    ValidateChallengesPresenter,
)
from challenges.domain.challenge import Challenge
from challenges.use_cases.validateChallenges.Interactor import (
    ValidateChallengesInteractor,
)


def _challenge(slug):
    return Challenge(
        name=f"Challenge {slug}",
        slug=slug,
        challenge_date=date(2026, 10, 15),
        difficulty=1,
        category="social",
        tone="friendly",
        required_action="respond warmly",
    )


class InMemoryChallengeRepository:
    def __init__(self, challenges=()):
        self.records = tuple(challenges)

    def list(self):
        return self.records


@dataclass
class FakeValidationGateway:
    database_errors_result: tuple[str, ...] = ()
    environment_errors_result: tuple[str, ...] = ()
    challenge_errors_result: dict[str, tuple[str, ...]] | None = None
    error: Exception | None = None

    def __post_init__(self):
        if self.challenge_errors_result is None:
            self.challenge_errors_result = {}
        self.checked = []

    def database_errors(self):
        if self.error is not None:
            raise self.error
        return self.database_errors_result

    def environment_errors(self):
        return self.environment_errors_result

    def challenge_errors(self, challenge):
        self.checked.append(challenge.slug)
        return self.challenge_errors_result.get(challenge.slug, ())


class ValidateChallengesInteractorTests(SimpleTestCase):
    def _run(self, *, challenges=(), validation):
        presenter = ValidateChallengesPresenter()
        interactor = ValidateChallengesInteractor(
            challenges=InMemoryChallengeRepository(challenges),
            validation=validation,
            presenter=presenter,
        )
        ValidateChallengesController(interactor).execute()
        return presenter.view_model

    def test_reports_success_when_all_checks_pass(self):
        challenge = _challenge("greeting")
        validation = FakeValidationGateway(challenge_errors_result={challenge.slug: ()})

        view_model = self._run(challenges=[challenge], validation=validation)

        self.assertTrue(view_model.success)
        self.assertEqual(view_model.message, "OK")
        self.assertEqual(view_model.errors, ())
        self.assertEqual(validation.checked, ["greeting"])

    def test_reports_validation_errors_and_skips_challenge_checks(self):
        validation = FakeValidationGateway(
            environment_errors_result=("MEDIA_ROOT is missing",)
        )

        view_model = self._run(
            challenges=[_challenge("greeting")], validation=validation
        )

        self.assertFalse(view_model.success)
        self.assertEqual(view_model.message, "Challenge validation failed.")
        self.assertEqual(view_model.errors, ("MEDIA_ROOT is missing",))
        self.assertEqual(validation.checked, [])

    def test_validates_challenges_in_slug_order(self):
        validation = FakeValidationGateway()

        self._run(
            challenges=[_challenge("zulu"), _challenge("alpha")],
            validation=validation,
        )

        self.assertEqual(validation.checked, ["alpha", "zulu"])

    def test_reports_gateway_failure(self):
        validation = FakeValidationGateway(error=RuntimeError("boom"))

        view_model = self._run(validation=validation)

        self.assertFalse(view_model.success)
        self.assertEqual(view_model.message, "Could not validate challenges: boom")
        self.assertEqual(view_model.errors, ())
