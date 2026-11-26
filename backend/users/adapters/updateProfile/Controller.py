import json

from users.domain.profileChanges import ProfileChanges
from users.useCases.updateProfile.InputBoundary import UpdateProfileInputBoundary
from users.useCases.updateProfile.InputData import UpdateProfileInputData
from users.useCases.updateProfile.OutputBoundary import UpdateProfileOutputBoundary
from users.useCases.updateProfile.OutputData import UpdateProfileFailureData


class UpdateProfileController:
    def __init__(
        self,
        interactor: UpdateProfileInputBoundary,
        presenter: UpdateProfileOutputBoundary,
    ):
        self._interactor = interactor
        self._presenter = presenter

    def execute(
        self, *, username: str, user_id: int | None, body: bytes, content_type: str
    ) -> None:
        try:
            if content_type != "application/json":
                raise ValueError("Expected an application/json body.")
            try:
                payload = json.loads(body)
            except ValueError, UnicodeDecodeError:
                raise ValueError("Expected a valid JSON object.")
            if not isinstance(payload, dict):
                raise ValueError("Expected a JSON object.")
            if set(payload) - {"slug", "name", "team", "avatar", "email"}:
                raise ValueError("Unexpected profile fields.")
            if payload.get("slug", username) != username:
                raise ValueError("slug must match the user in the request URL.")
            fields = {key: value for key, value in payload.items() if key != "slug"}
            if any(not isinstance(value, str) for value in fields.values()):
                raise ValueError("Profile fields must be strings.")
            changes = ProfileChanges(**fields)
        except ValueError as exc:
            self._presenter.prepare_fail_view(
                UpdateProfileFailureData("invalid", str(exc))
            )
            return
        self._interactor.execute(
            UpdateProfileInputData(username=username, user_id=user_id, changes=changes)
        )
