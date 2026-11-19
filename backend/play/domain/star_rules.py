from dataclasses import dataclass
from math import isfinite


@dataclass(frozen=True, slots=True)
class StarRules:
    timed_star_seconds: float = 10

    def __post_init__(self):
        if (
            isinstance(self.timed_star_seconds, bool)
            or not isinstance(self.timed_star_seconds, (int, float))
            or not isfinite(self.timed_star_seconds)
            or self.timed_star_seconds < 0
        ):
            raise ValueError("Star time limit must be a finite, non-negative number.")

    def score(self, tone_correct, tone_time_seconds, action_correct):
        if not isinstance(tone_correct, bool) or not isinstance(action_correct, bool):
            raise ValueError("Tone and action results must be booleans.")
        if (
            isinstance(tone_time_seconds, bool)
            or not isinstance(tone_time_seconds, (int, float))
            or not isfinite(tone_time_seconds)
            or tone_time_seconds < 0
        ):
            raise ValueError("Tone time must be a finite, non-negative number.")
        return (
            int(tone_correct)
            + int(tone_time_seconds <= self.timed_star_seconds)
            + int(action_correct)
        )
