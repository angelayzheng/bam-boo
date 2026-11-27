from collections.abc import Callable

from users.useCases.ports import AuthenticatedAccount
from users.useCases.signUp.OutputData import SignUpOutputData


class SignUpPresenter:
    def __init__(self, csrf_token: Callable[[], str]):
        self._csrf_token = csrf_token
        self.response_body: dict = {}
        self.status_code = 201

    def present(self, output: SignUpOutputData) -> None:
        self.status_code = output.status_code
        if output.account is None:
            self.response_body = {"errors": output.errors or {}}
            return
        self.response_body = {
            "user": _account_body(output.account),
            "csrfToken": self._csrf_token(),
        }


def _account_body(account: AuthenticatedAccount) -> dict:
    return {"id": account.user_id, "username": account.username, "email": account.email}
