from users.adapters.profileData import username_profile_data
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
            else {
                "user_id": profile.user_id,
                "username": profile.username,
                "avatar": profile.avatar,
                "total_score": profile.total_score,
                "completed_challenges": len(profile.scores),
                "scores": dict(profile.scores),
            }
        )
        self.status_code = 200

    def prepare_fail_view(self) -> None:
        self.response_body = {"detail": "Profile not found."}
        self.status_code = 404
