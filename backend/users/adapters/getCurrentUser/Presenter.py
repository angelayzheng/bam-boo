from collections.abc import Callable

from users.useCases.getCurrentUser.OutputBoundary import GetCurrentUserOutputBoundary
from users.useCases.getCurrentUser.OutputData import GetCurrentUserOutputData


class GetCurrentUserPresenter(GetCurrentUserOutputBoundary):
    def __init__(self, csrf_token: Callable[[], str]):
        self._csrf_token = csrf_token
        self.response_body: dict = {}
        self.status_code = 200

    def prepare_success_view(self, output_data: GetCurrentUserOutputData) -> None:
        self.response_body = {
            "user": {
                "id": output_data.user_id,
                "username": output_data.username,
                "email": output_data.email,
            },
            "csrfToken": self._csrf_token(),
        }
        self.status_code = 200

    def prepare_fail_view(self) -> None:
        self.response_body = {"detail": "Authentication required."}
        self.status_code = 401
