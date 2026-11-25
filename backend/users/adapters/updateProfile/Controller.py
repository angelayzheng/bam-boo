import json

from users.useCases.updateProfile.InputBoundary import UpdateProfileInputBoundary
from users.useCases.updateProfile.InputData import UpdateProfileInputData


class UpdateProfileController:
    def __init__(self, interactor: UpdateProfileInputBoundary):
        self._interactor = interactor

    def execute(
        self, *, username: str, user_id: int | None, body: bytes, content_type: str
    ) -> None:
        payload = None
        error = None
        if content_type != "application/json":
            error = "Expected an application/json body."
        else:
            try:
                payload = json.loads(body)
            except ValueError, UnicodeDecodeError:
                error = "Expected a valid JSON object."
            else:
                if not isinstance(payload, dict):
                    error = "Expected a JSON object."
        self._interactor.execute(
            UpdateProfileInputData(
                username=username, user_id=user_id, payload=payload, parsing_error=error
            )
        )
