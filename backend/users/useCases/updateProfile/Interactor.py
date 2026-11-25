from users.domain.profileChanges import ProfileCollectionError, validate_profile_changes
from users.useCases.ports import (
    EmailValidator,
    ProfileDetailsRepository,
    TeamRepository,
    UnitOfWork,
)

from .InputBoundary import UpdateProfileInputBoundary
from .InputData import UpdateProfileInputData
from .OutputBoundary import UpdateProfileOutputBoundary
from .OutputData import UpdateProfileFailureData, UpdateProfileOutputData


class UpdateProfileInteractor(UpdateProfileInputBoundary):
    def __init__(
        self,
        *,
        profiles: ProfileDetailsRepository,
        teams: TeamRepository,
        email_validator: EmailValidator,
        unit_of_work: UnitOfWork,
        presenter: UpdateProfileOutputBoundary,
    ):
        self._profiles = profiles
        self._teams = teams
        self._email_validator = email_validator
        self._unit_of_work = unit_of_work
        self._presenter = presenter

    def _fail(self, reason, message):
        self._presenter.prepare_fail_view(UpdateProfileFailureData(reason, message))

    def execute(self, input_data: UpdateProfileInputData) -> None:
        if input_data.user_id is None:
            self._fail("unauthenticated", "Authentication required.")
            return
        with self._unit_of_work.atomic():
            profile = self._profiles.get_by_username(
                input_data.username, for_update=True
            )
            if profile is None:
                self._fail("not_found", "Profile not found.")
                return
            if input_data.user_id != profile.user_id:
                self._fail("forbidden", "You can only update your own profile.")
                return
            if input_data.parsing_error:
                self._fail("invalid", input_data.parsing_error)
                return
            if not isinstance(input_data.payload, dict):
                self._fail("invalid", "Expected a JSON object.")
                return
            try:
                changes = validate_profile_changes(
                    input_data.payload,
                    username=profile.username,
                    current_total=profile.total_score,
                )
                if changes.get("email") and not self._email_validator.is_valid(
                    changes["email"]
                ):
                    raise ValueError("email must be a valid email address.")
                if "team" in changes:
                    matches = (
                        self._teams.find_by_slug(changes["team"])
                        if changes["team"]
                        else []
                    )
                    if changes["team"] and len(matches) != 1:
                        raise ValueError(
                            "team must match an existing, unique team slug."
                        )
                    changes["group_id"] = matches[0] if matches else None
            except ProfileCollectionError as exc:
                self._presenter.prepare_fail_view(
                    UpdateProfileFailureData("invalid", str(exc), collection_error=True)
                )
                return
            except ValueError as exc:
                self._fail("invalid", str(exc))
                return
            updated = self._profiles.update(profile.user_id, changes)
        self._presenter.prepare_success_view(UpdateProfileOutputData(profile=updated))
