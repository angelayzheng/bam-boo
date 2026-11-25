from users.useCases.profileData import ProfileData


def username_profile_data(profile: ProfileData) -> dict:
    return {
        "slug": profile.username,
        "challenge_scores": dict(profile.scores),
        "total_score": float(profile.total_score),
        "name": profile.name or profile.username,
        "team": profile.team,
        "login_days": sorted(profile.login_days),
        "avatar": profile.avatar,
        "email": profile.email,
    }
