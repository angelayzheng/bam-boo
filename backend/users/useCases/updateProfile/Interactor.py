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
            changes = input_data.changes
            if changes.email and not self._email_validator.is_valid(changes.email):
                self._fail("invalid", "email must be a valid email address.")
                return
            group_id = None
            if changes.team:
                matches = self._teams.find_by_slug(changes.team)
                if len(matches) != 1:
                    self._fail(
                        "invalid", "team must match an existing, unique team slug."
                    )
                    return
                group_id = matches[0]
            updated = self._profiles.update(profile.user_id, changes, group_id=group_id)
        self._presenter.prepare_success_view(UpdateProfileOutputData(profile=updated))
