from users.adapters.profileData import profile_progress_data, username_profile_data
from users.useCases.viewProfile.OutputBoundary import ViewProfileOutputBoundary
from users.useCases.viewProfile.OutputData import ViewProfileOutputData


class ViewProfilePresenter(ViewProfileOutputBoundary):
    def __init__(self):
        self.response_body: dict = {}
        self.status_code = 200

    def prepare_success_view(self, output_data: ViewProfileOutputData) -> None:
        profile = output_data.profile
        self.response_body = (
            username_profile_data(profile)
            if output_data.by_username
            else profile_progress_data(
                user_id=profile.user_id,
                username=profile.username,
                avatar=profile.avatar,
                total_score=profile.total_score,
                scores=profile.scores,
            )
        )
        self.status_code = 200

    def prepare_fail_view(self) -> None:
        self.response_body = {"detail": "Profile not found."}
        self.status_code = 404
