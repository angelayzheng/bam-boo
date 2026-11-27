from users.useCases.logIn.InputData import LogInInputData


class LogInController:
    def __init__(self, interactor):
        self._interactor = interactor

    def execute(self, *, username: str, password: str) -> None:
        self._interactor.execute(LogInInputData(username, password))
