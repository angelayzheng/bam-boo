from users.useCases.ports import AuthenticationGateway

from .OutputBoundary import LogOutOutputBoundary
from .OutputData import LogOutOutputData


class LogOutInteractor:
    def __init__(
        self, *, authentication: AuthenticationGateway, presenter: LogOutOutputBoundary
    ):
        self._authentication = authentication
        self._presenter = presenter

    def execute(self) -> None:
        self._authentication.end_session()
        self._presenter.present(LogOutOutputData())
