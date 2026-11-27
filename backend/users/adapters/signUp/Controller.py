from users.useCases.signUp.InputData import SignUpInputData


class SignUpController:
    def __init__(self, interactor):
        self._interactor = interactor

    def execute(
        self, *, username: str, password: str, email: str, group_id: int | None
    ):
        self._interactor.execute(SignUpInputData(username, password, email, group_id))
