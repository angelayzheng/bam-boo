from datetime import date
from math import isfinite


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


def validate_profile_changes(
    payload: dict, *, username: str, current_total: int
) -> dict:
    allowed = {
        "slug",
        "challenge_scores",
        "total_score",
        "name",
        "team",
        "login_days",
        "avatar",
        "email",
    }
    if set(payload) - allowed:
        raise ValueError("Unexpected profile fields.")
    if payload.get("slug", username) != username:
        raise ValueError("slug must match the user in the request URL.")
    changes = dict(payload)
    expected_total = current_total
    if "challenge_scores" in payload:
        validate_scores(payload["challenge_scores"])
        expected_total = sum(payload["challenge_scores"].values())
        changes["total_score"] = expected_total
    if "total_score" in payload:
        total = payload["total_score"]
        if (
            isinstance(total, bool)
            or not isinstance(total, (int, float))
            or (isinstance(total, float) and not isfinite(total))
            or total != expected_total
        ):
            raise ValueError("total_score must equal the sum of challenge_scores.")
    if "name" in payload:
        name = payload["name"]
        if not isinstance(name, str) or not name.strip() or len(name.strip()) > 150:
            raise ValueError(
                "name must be a non-empty string of at most 150 characters."
            )
        changes["name"] = name.strip()
    if "team" in payload and not isinstance(payload["team"], str):
        raise ValueError("team must be a string.")
    if "login_days" in payload:
        validate_login_days(payload["login_days"])
        changes["login_days"] = sorted(payload["login_days"])
    if "avatar" in payload and payload["avatar"] not in AVATARS:
        raise ValueError("avatar must be one of the supported avatar values.")
    if "email" in payload and (
        not isinstance(payload["email"], str) or len(payload["email"]) > 254
    ):
        raise ValueError("email must be a string of at most 254 characters.")
    return changes
