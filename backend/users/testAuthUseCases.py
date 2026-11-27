from django.test import SimpleTestCase

from users.adapters.logIn.Presenter import LogInPresenter
from users.adapters.logOut.Presenter import LogOutPresenter
from users.adapters.signUp.Presenter import SignUpPresenter
from users.useCases.logIn.InputData import LogInInputData
from users.useCases.logIn.Interactor import LogInInteractor
from users.useCases.logOut.Interactor import LogOutInteractor
from users.useCases.ports import (
    AccountCreationResult,
    AuthenticatedAccount,
)
from users.useCases.signUp.InputData import SignUpInputData
from users.useCases.signUp.Interactor import SignUpInteractor


class FakeAuthenticationGateway:
    def __init__(self, account=None, errors=None):
        self.account = account
        self.errors = errors or {}
        self.started_sessions = []
        self.ended_sessions = 0
        self.created = []

    def create_account(self, **values):
        self.created.append(values)
        return AccountCreationResult(self.account, self.errors)

    def authenticate(self, **values):
        return self.account

    def start_session(self, user_id):
        self.started_sessions.append(user_id)

    def end_session(self):
        self.ended_sessions += 1


class AuthUseCaseTests(SimpleTestCase):
    def setUp(self):
        self.account = AuthenticatedAccount(7, "ada", "ada@example.com")

    def test_sign_up_creates_account_starts_session_and_presents_account(self):
        gateway = FakeAuthenticationGateway(account=self.account)
        presenter = SignUpPresenter(lambda: "csrf")

        SignUpInteractor(authentication=gateway, presenter=presenter).execute(
            SignUpInputData("ada", "secret", "ada@example.com", 3)
        )

        self.assertEqual(gateway.created[0]["group_id"], 3)
        self.assertEqual(gateway.started_sessions, [7])
        self.assertEqual(presenter.status_code, 201)
        self.assertEqual(presenter.response_body["user"]["id"], 7)
        self.assertEqual(presenter.response_body["csrfToken"], "csrf")

    def test_sign_up_validation_errors_do_not_start_session(self):
        gateway = FakeAuthenticationGateway(errors={"username": ["Taken."]})
        presenter = SignUpPresenter(lambda: "unused")

        SignUpInteractor(authentication=gateway, presenter=presenter).execute(
            SignUpInputData("ada", "secret")
        )

        self.assertEqual(gateway.started_sessions, [])
        self.assertEqual(presenter.status_code, 400)
        self.assertEqual(presenter.response_body, {"errors": {"username": ["Taken."]}})

    def test_log_in_rejects_missing_account_or_starts_session(self):
        rejected_gateway = FakeAuthenticationGateway()
        rejected_presenter = LogInPresenter(lambda: "unused")
        LogInInteractor(
            authentication=rejected_gateway, presenter=rejected_presenter
        ).execute(LogInInputData("ada", "wrong"))
        self.assertEqual(rejected_presenter.status_code, 401)
        self.assertEqual(rejected_gateway.started_sessions, [])

        accepted_gateway = FakeAuthenticationGateway(account=self.account)
        accepted_presenter = LogInPresenter(lambda: "csrf")
        LogInInteractor(
            authentication=accepted_gateway, presenter=accepted_presenter
        ).execute(LogInInputData("ada", "secret"))
        self.assertEqual(accepted_gateway.started_sessions, [7])
        self.assertEqual(accepted_presenter.status_code, 200)
        self.assertEqual(accepted_presenter.response_body["user"]["username"], "ada")

    def test_log_out_ends_session_and_presents_success(self):
        gateway = FakeAuthenticationGateway()
        presenter = LogOutPresenter()

        LogOutInteractor(authentication=gateway, presenter=presenter).execute()

        self.assertEqual(gateway.ended_sessions, 1)
        self.assertEqual(presenter.status_code, 200)
        self.assertEqual(presenter.response_body, {"detail": "Logged out."})
