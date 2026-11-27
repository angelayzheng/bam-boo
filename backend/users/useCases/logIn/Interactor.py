from users.useCases.ports import AuthenticationGateway

from .InputData import LogInInputData
from .OutputBoundary import LogInOutputBoundary
from .OutputData import LogInOutputData


class LogInInteractor:
    def __init__(
        self, *, authentication: AuthenticationGateway, presenter: LogInOutputBoundary
    ):
        self._authentication = authentication
        self._presenter = presenter

    def execute(self, data: LogInInputData) -> None:
        account = self._authentication.authenticate(
            username=data.username, password=data.password
        )
        if account is None:
            self._presenter.present(LogInOutputData(401))
            return
        self._authentication.start_session(account.user_id)
        self._presenter.present(LogInOutputData(200, account=account))
