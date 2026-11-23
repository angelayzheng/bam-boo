from dataclasses import dataclass

from django.test import SimpleTestCase

from challenges.adapters.validateChallenges.Controller import (
    ValidateChallengesController,
)
from challenges.adapters.validateChallenges.Presenter import (
    ValidateChallengesPresenter,
)
from challenges.use_cases.validateChallenges.Interactor import (
    ValidateChallengesInteractor,
)


@dataclass
class FakeValidationGateway:
    database_errors_result: tuple[str, ...] = ()
    environment_errors_result: tuple[str, ...] = ()
    challenge_errors_result: tuple[str, ...] = ()
    error: Exception | None = None
    challenge_error: Exception | None = None

    def __post_init__(self):
        self.challenge_calls = 0

    def database_errors(self):
        if self.error is not None:
            raise self.error
        return self.database_errors_result

    def environment_errors(self):
        return self.environment_errors_result

    def challenge_errors(self):
        self.challenge_calls += 1
        if self.challenge_error is not None:
            raise self.challenge_error
        return self.challenge_errors_result


class ValidateChallengesInteractorTests(SimpleTestCase):
    def _run(self, *, validation):
        presenter = ValidateChallengesPresenter()
        interactor = ValidateChallengesInteractor(
            validation=validation,
            presenter=presenter,
        )
        ValidateChallengesController(interactor).execute()
        return presenter.view_model

    def test_reports_success_when_all_checks_pass(self):
        validation = FakeValidationGateway()

        view_model = self._run(validation=validation)

        self.assertTrue(view_model.success)
        self.assertEqual(view_model.message, "OK")
        self.assertEqual(view_model.errors, ())
        self.assertEqual(validation.challenge_calls, 1)

    def test_reports_database_errors_and_skips_challenge_checks(self):
        validation = FakeValidationGateway(
            database_errors_result=("Unapplied migrations: tone.0002.",)
        )

        view_model = self._run(validation=validation)

        self.assertFalse(view_model.success)
        self.assertEqual(view_model.message, "Challenge validation failed.")
        self.assertEqual(view_model.errors, ("Unapplied migrations: tone.0002.",))
        self.assertEqual(validation.challenge_calls, 0)

    def test_reports_database_and_environment_errors_together(self):
        validation = FakeValidationGateway(
            database_errors_result=("SQLite integrity_check failed",),
            environment_errors_result=("MEDIA_ROOT is missing",),
        )

        view_model = self._run(validation=validation)

        self.assertFalse(view_model.success)
        self.assertEqual(view_model.message, "Challenge validation failed.")
        self.assertEqual(
            view_model.errors,
            ("SQLite integrity_check failed", "MEDIA_ROOT is missing"),
        )
        self.assertEqual(validation.challenge_calls, 0)

    def test_reports_challenge_validation_errors(self):
        validation = FakeValidationGateway(
            challenge_errors_result=("greeting: media file is missing.",)
        )

        view_model = self._run(validation=validation)

        self.assertFalse(view_model.success)
        self.assertEqual(view_model.message, "Challenge validation failed.")
        self.assertEqual(view_model.errors, ("greeting: media file is missing.",))
        self.assertEqual(validation.challenge_calls, 1)

    def test_reports_validation_errors_and_skips_challenge_checks(self):
        validation = FakeValidationGateway(
            environment_errors_result=("MEDIA_ROOT is missing",)
        )

        view_model = self._run(validation=validation)

        self.assertFalse(view_model.success)
        self.assertEqual(view_model.message, "Challenge validation failed.")
        self.assertEqual(view_model.errors, ("MEDIA_ROOT is missing",))
        self.assertEqual(validation.challenge_calls, 0)

    def test_reports_gateway_failure(self):
        validation = FakeValidationGateway(error=RuntimeError("boom"))

        view_model = self._run(validation=validation)

        self.assertFalse(view_model.success)
        self.assertEqual(view_model.message, "Could not validate challenges: boom")
        self.assertEqual(view_model.errors, ())
        self.assertEqual(validation.challenge_calls, 0)

    def test_reports_challenge_check_failure(self):
        validation = FakeValidationGateway(challenge_error=RuntimeError("boom"))

        view_model = self._run(validation=validation)

        self.assertFalse(view_model.success)
        self.assertEqual(view_model.message, "Could not validate challenges: boom")
        self.assertEqual(view_model.errors, ())
