from users.useCases.ports import ProfileDetailsRepository

from .InputBoundary import ViewProfileInputBoundary
from .InputData import ViewProfileInputData
from .OutputBoundary import ViewProfileOutputBoundary
from .OutputData import ViewProfileOutputData


class ViewProfileInteractor(ViewProfileInputBoundary):
    def __init__(
        self,
        *,
        profiles: ProfileDetailsRepository,
        presenter: ViewProfileOutputBoundary,
    ):
        self._profiles = profiles
        self._presenter = presenter

    def execute(self, input_data: ViewProfileInputData) -> None:
        by_username = input_data.username is not None
        profile = (
            self._profiles.get_by_username(input_data.username)
            if by_username
            else self._profiles.get_by_user_id(input_data.user_id)
        )
        if profile is None:
            self._presenter.prepare_fail_view()
            return
        self._presenter.prepare_success_view(
            ViewProfileOutputData(profile=profile, by_username=by_username)
        )
