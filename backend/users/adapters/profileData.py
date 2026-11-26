from users.useCases.profileData import ProfileData


def profile_progress_data(
    *,
    user_id: int,
    username: str,
    avatar: str,
    total_score: int,
    scores: dict[str, int],
) -> dict:
    return {
        "user_id": user_id,
        "username": username,
        "avatar": avatar,
        "total_score": total_score,
        "completed_challenges": len(scores),
        "scores": dict(scores),
    }


def username_profile_data(profile: ProfileData) -> dict:
    return {
        "slug": profile.username,
        "challenge_scores": dict(profile.scores),
        "total_score": float(profile.total_score),
        "name": profile.name or profile.username,
        "team": profile.team,
        "login_days": sorted(profile.login_days),
        "avatar": profile.avatar,
    }
