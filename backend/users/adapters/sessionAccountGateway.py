from users.useCases.getCurrentUser.OutputData import GetCurrentUserOutputData
from users.useCases.ports import CurrentAccountGateway


class DjangoSessionAccountGateway(CurrentAccountGateway):
    def __init__(self, request):
        self._request = request

    def current_account(self) -> GetCurrentUserOutputData | None:
        user = self._request.user
        if not user.is_authenticated:
            return None
        return GetCurrentUserOutputData(
            user_id=user.pk, username=user.username, email=user.email
        )
