from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import date, timedelta


@dataclass(slots=True)
class Profile:
    user_id: int
    username: str
    avatar: str = "fox"
    team: str | None = None
    scores: dict[str, int] = field(default_factory=dict)
    login_days: list[date] = field(default_factory=list)

    def __post_init__(self):
        if not isinstance(self.user_id, int) or isinstance(self.user_id, bool):
            raise ValueError("Profile user ID must be an integer.")
        if not isinstance(self.username, str) or not self.username.strip():
            raise ValueError("Profile username must not be empty.")
        if not isinstance(self.scores, Mapping):
            raise ValueError("Profile scores must be a mapping.")
        if not isinstance(self.login_days, (list, tuple)):
            raise ValueError("Profile login days must be a sequence of dates.")
        self.scores = dict(self.scores)
        if any(type(day) is not date for day in self.login_days):
            raise ValueError("Profile login days must be dates.")
        if len(set(self.login_days)) != len(self.login_days):
            raise ValueError("Profile login days must not contain duplicates.")
        self.login_days = sorted(self.login_days)
        for challenge_slug, score in self.scores.items():
            if not isinstance(challenge_slug, str) or not challenge_slug.strip():
                raise ValueError("Score challenge slugs must not be empty.")
            _validate_score(score)

    @property
    def total_score(self):
        return sum(self.scores.values())

    def add_score(self, challenge_slug, score):
        if not isinstance(challenge_slug, str) or not challenge_slug.strip():
            raise ValueError("Score challenge slug must not be empty.")
        _validate_score(score)
        self.scores[challenge_slug] = max(self.scores.get(challenge_slug, 0), score)

    def record_login(self, day=None):
        login_day = date.today() if day is None else day
        if type(login_day) is not date:
            raise ValueError("Login day must be a date.")
        if login_day not in self.login_days:
            self.login_days.append(login_day)
            self.login_days.sort()

    def streak(self, today=None):
        today = date.today() if today is None else today
        if type(today) is not date:
            raise ValueError("Streak reference must be a date.")
        days = set(self.login_days)
        current = today if today in days else today - timedelta(days=1)
        if current not in days:
            return 0
        count = 0
        while current in days:
            count += 1
            current -= timedelta(days=1)
        return count


def _validate_score(score):
    if isinstance(score, bool) or not isinstance(score, int) or not 0 <= score <= 3:
        raise ValueError("Score must be a whole number between 0 and 3.")
