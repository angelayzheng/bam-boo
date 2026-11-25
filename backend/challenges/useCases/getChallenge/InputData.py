from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GetChallengeInputData:
    slug: str
