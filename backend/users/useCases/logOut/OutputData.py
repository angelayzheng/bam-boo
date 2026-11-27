from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class LogOutOutputData:
    status_code: int = 200
