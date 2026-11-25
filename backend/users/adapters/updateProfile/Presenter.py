from users.adapters.profileData import username_profile_data
from users.useCases.updateProfile.OutputBoundary import UpdateProfileOutputBoundary
from users.useCases.updateProfile.OutputData import (
    UpdateProfileFailureData,
    UpdateProfileOutputData,
)


class UpdateProfilePresenter(UpdateProfileOutputBoundary):
    def __init__(self):
        self.response_body: dict = {}
        self.status_code = 200

    def prepare_success_view(self, output_data: UpdateProfileOutputData) -> None:
        self.response_body = username_profile_data(output_data.profile)
        self.status_code = 200

    def prepare_fail_view(self, failure: UpdateProfileFailureData) -> None:
        self.response_body = {
            "detail": (
                str([failure.message]) if failure.collection_error else failure.message
            )
        }
        self.status_code = {
            "unauthenticated": 401,
            "not_found": 404,
            "forbidden": 403,
            "invalid": 400,
        }[failure.reason]
