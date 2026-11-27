from collections.abc import Callable

from users.useCases.ports import AuthenticatedAccount
from users.useCases.logIn.OutputData import LogInOutputData


class LogInPresenter:
    def __init__(self, csrf_token: Callable[[], str]):
        self._csrf_token = csrf_token
        self.response_body: dict = {}
        self.status_code = 200

    def present(self, output: LogInOutputData) -> None:
        self.status_code = output.status_code
        if output.account is None:
            self.response_body = {"detail": "Invalid username or password."}
            return
        account: AuthenticatedAccount = output.account
        self.response_body = {
            "user": {
                "id": account.user_id,
                "username": account.username,
                "email": account.email,
            },
            "csrfToken": self._csrf_token(),
        }
