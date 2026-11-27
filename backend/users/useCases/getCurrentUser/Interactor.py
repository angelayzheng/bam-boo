from users.useCases.ports import CurrentAccountGateway

from .InputBoundary import GetCurrentUserInputBoundary
from .OutputBoundary import GetCurrentUserOutputBoundary


class GetCurrentUserInteractor(GetCurrentUserInputBoundary):
    def __init__(
        self,
        *,
        accounts: CurrentAccountGateway,
        presenter: GetCurrentUserOutputBoundary,
    ):
        self._accounts = accounts
        self._presenter = presenter

    def execute(self) -> None:
        account = self._accounts.current_account()
        if account is None:
            self._presenter.prepare_fail_view()
            return
        self._presenter.prepare_success_view(account)
