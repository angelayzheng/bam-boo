from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class Attempt:
    submission_id: str
    profile_id: int
    challenge_slug: str
    score: int
    completed_at: datetime
    received_at: datetime | None = None
    record_id: int | None = None

    def __post_init__(self):
        if not isinstance(self.submission_id, str) or not self.submission_id.strip():
            raise ValueError("Attempt submission ID must not be empty.")
        if isinstance(self.profile_id, bool) or not isinstance(self.profile_id, int):
            raise ValueError("Attempt profile ID must be an integer.")
        if not isinstance(self.challenge_slug, str) or not self.challenge_slug.strip():
            raise ValueError("Attempt challenge slug must not be empty.")
        if isinstance(self.score, bool) or not isinstance(self.score, int):
            raise ValueError("Attempt score must be a whole number.")
        if not 0 <= self.score <= 3:
            raise ValueError("Attempt score must be between 0 and 3.")
        if self.record_id is not None and (
            isinstance(self.record_id, bool) or not isinstance(self.record_id, int)
        ):
            raise ValueError("Attempt record ID must be an integer.")
        if (
            not isinstance(self.completed_at, datetime)
            or self.completed_at.utcoffset() is None
        ):
            raise ValueError("Attempt completion time must be timezone-aware.")
        if self.received_at is not None and (
            not isinstance(self.received_at, datetime)
            or self.received_at.utcoffset() is None
        ):
            raise ValueError("Attempt received time must be timezone-aware.")

    def matches_completion(self, profile_id, challenge_slug, score, completed_at):
        return (
            self.profile_id == profile_id
            and self.challenge_slug == challenge_slug
            and self.score == score
            and self.completed_at == completed_at
        )
