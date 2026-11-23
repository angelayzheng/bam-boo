from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date, datetime

from .challenge import Challenge


class ChallengePackageError(Exception):
    """A challenge package cannot be loaded, validated, or installed."""


class AudioValidationError(Exception):
    """An audio file cannot be validated as playable MP3 audio."""


@dataclass(frozen=True, slots=True)
class ChallengePackageMetadata:
    name: str
    slug: str
    challenge_date: date
    difficulty: int
    category: str
    tone: str
    required_action: str


def challenge_from_package(
    metadata: Mapping[str, object], conversation_tree: Mapping[str, object]
) -> Challenge:
    """Build the domain challenge described by a validated package."""
    try:
        raw_date = metadata["challenge_date"]
        if isinstance(raw_date, datetime):
            challenge_date = raw_date.date()
        elif isinstance(raw_date, date):
            challenge_date = raw_date
        else:
            challenge_date = date.fromisoformat(str(raw_date))
        return Challenge(
            name=str(metadata["name"]),
            slug=str(metadata["slug"]),
            challenge_date=challenge_date,
            difficulty=int(metadata["difficulty"]),
            category=str(metadata["category"]),
            tone=str(metadata["tone"]),
            required_action=str(metadata["required_action"]),
            conversation_tree=conversation_tree,
        )
    except ChallengePackageError:
        raise
    except (KeyError, TypeError, ValueError) as exc:
        raise ChallengePackageError(str(exc)) from exc
