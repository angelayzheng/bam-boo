from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class LogInInputData:
    username: str
    password: str
