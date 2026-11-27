from users.useCases.ports import AuthenticationGateway

from .InputData import SignUpInputData
from .OutputBoundary import SignUpOutputBoundary
from .OutputData import SignUpOutputData


class SignUpInteractor:
    def __init__(
        self, *, authentication: AuthenticationGateway, presenter: SignUpOutputBoundary
    ):
        self._authentication = authentication
        self._presenter = presenter

    def execute(self, data: SignUpInputData) -> None:
        result = self._authentication.create_account(
            username=data.username,
            password=data.password,
            email=data.email,
            group_id=data.group_id,
        )
        if result.account is None:
            self._presenter.present(SignUpOutputData(400, errors=result.errors))
            return
        self._authentication.start_session(result.account.user_id)
        self._presenter.present(SignUpOutputData(201, account=result.account))
