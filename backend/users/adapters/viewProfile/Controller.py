from users.useCases.viewProfile.InputBoundary import ViewProfileInputBoundary
from users.useCases.viewProfile.InputData import ViewProfileInputData


class ViewProfileController:
    def __init__(self, interactor: ViewProfileInputBoundary):
        self._interactor = interactor

    def execute(
        self, *, user_id: int | None = None, username: str | None = None
    ) -> None:
        self._interactor.execute(
            ViewProfileInputData(user_id=user_id, username=username)
        )
