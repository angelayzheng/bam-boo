from unittest import TestCase

from users.adapters.getCurrentUser.Controller import GetCurrentUserController
from users.adapters.getCurrentUser.Presenter import GetCurrentUserPresenter
from users.useCases.getCurrentUser.Interactor import GetCurrentUserInteractor
from users.useCases.getCurrentUser.OutputData import GetCurrentUserOutputData


class RecordingOutput:
    def __init__(self):
        self.successes = []
        self.failures = []

    def prepare_success_view(self, output):
        self.successes.append(output)

    def prepare_fail_view(self, failure=None):
        self.failures.append(failure)


class FakeAccounts:
    account = None

    def current_account(self):
        return self.account


class GetCurrentUserTests(TestCase):
    def test_anonymous_and_signed_in_accounts_use_the_output_boundary(self):
        accounts = FakeAccounts()
        output = RecordingOutput()
        interactor = GetCurrentUserInteractor(accounts=accounts, presenter=output)
        interactor.execute()
        self.assertEqual(output.failures, [None])
        self.assertEqual(output.successes, [])
        accounts.account = GetCurrentUserOutputData(7, "ada", "ada@example.com")
        interactor.execute()
        self.assertEqual(output.successes, [accounts.account])

    def test_presenter_adds_csrf_only_on_success_and_resets_status(self):
        accounts = FakeAccounts()
        tokens = []
        presenter = GetCurrentUserPresenter(lambda: tokens.append(True) or "token")
        controller = GetCurrentUserController(
            GetCurrentUserInteractor(accounts=accounts, presenter=presenter)
        )
        controller.execute()
        self.assertEqual(presenter.status_code, 401)
        self.assertEqual(tokens, [])
        accounts.account = GetCurrentUserOutputData(7, "ada", "ada@example.com")
        controller.execute()
        self.assertEqual(presenter.status_code, 200)
        self.assertEqual(
            presenter.response_body,
            {
                "user": {"id": 7, "username": "ada", "email": "ada@example.com"},
                "csrfToken": "token",
            },
        )
        accounts.account = None
        controller.execute()
        self.assertEqual(presenter.status_code, 401)
        self.assertEqual(
            presenter.response_body, {"detail": "Authentication required."}
        )
