from typing import Protocol


class GetCurrentUserInputBoundary(Protocol):
    def execute(self) -> None: ...
