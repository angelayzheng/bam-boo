from typing import Protocol


class LogOutInputBoundary(Protocol):
    def execute(self) -> None: ...
