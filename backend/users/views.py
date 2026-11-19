"""Compatibility exports for user endpoints."""

from users.adapters.auth_views import (
    csrf_token,
    current_user,
    login_user,
    logout_user,
    signup,
    signup_groups,
)
from users.adapters.progress_views import (
    leaderboard,
    save_challenge_score,
    user_by_slug,
    user_profile,
)
