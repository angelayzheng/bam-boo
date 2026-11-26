from dataclasses import dataclass
from datetime import date


class ProfileCollectionError(ValueError):
    """Invalid score-map or login-day collection values."""


AVATARS = ("fox", "owl", "bear", "cat", "robot", "ghost")


def validate_scores(value):
    if not isinstance(value, dict):
        raise ProfileCollectionError("Scores must be a JSON object.")
    for key, score in value.items():
        if not isinstance(key, str) or not key.strip():
            raise ProfileCollectionError("Score keys must be non-empty strings.")
        if isinstance(score, bool) or not isinstance(score, int):
            raise ProfileCollectionError(f"Score for {key!r} must be a whole number.")
        if not 0 <= score <= 3:
            raise ProfileCollectionError(f"Score for {key!r} must be between 0 and 3.")


def validate_login_days(value):
    if not isinstance(value, list):
        raise ProfileCollectionError("Login days must be a JSON list.")
    seen = set()
    for entry in value:
        if not isinstance(entry, str):
            raise ProfileCollectionError("Each login day must be a YYYY-MM-DD string.")
        try:
            date.fromisoformat(entry)
        except ValueError as exc:
            raise ProfileCollectionError(
                f"Invalid login day {entry!r}; expected YYYY-MM-DD."
            ) from exc
        if entry in seen:
            raise ProfileCollectionError(f"Duplicate login day: {entry!r}.")
        seen.add(entry)


@dataclass(frozen=True, slots=True)
class ProfileChanges:
    """Editable account details; None means a field was omitted."""

    name: str | None = None
    team: str | None = None
    avatar: str | None = None
    email: str | None = None

    def __post_init__(self):
        if self.name is not None:
            if (
                not isinstance(self.name, str)
                or not self.name.strip()
                or len(self.name.strip()) > 150
            ):
                raise ValueError(
                    "name must be a non-empty string of at most 150 characters."
                )
            object.__setattr__(self, "name", self.name.strip())
        if self.team is not None and not isinstance(self.team, str):
            raise ValueError("team must be a string.")
        if self.avatar is not None and self.avatar not in AVATARS:
            raise ValueError("avatar must be one of the supported avatar values.")
        if self.email is not None and (
            not isinstance(self.email, str) or len(self.email) > 254
        ):
            raise ValueError("email must be a string of at most 254 characters.")
