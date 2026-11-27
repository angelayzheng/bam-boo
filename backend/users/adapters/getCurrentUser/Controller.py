from users.useCases.getCurrentUser.InputBoundary import GetCurrentUserInputBoundary


class GetCurrentUserController:
    def __init__(self, interactor: GetCurrentUserInputBoundary):
        self._interactor = interactor

    def execute(self) -> None:
        self._interactor.execute()
