class LogOutController:
    def __init__(self, interactor):
        self._interactor = interactor

    def execute(self) -> None:
        self._interactor.execute()
