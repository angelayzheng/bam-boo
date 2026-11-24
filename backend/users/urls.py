from django.urls import path

from .adapters.views import (
    leaderboard,
    save_challenge_score,
    user_by_slug,
    user_profile,
    csrf_token,
    current_user,
    login_user,
    logout_user,
    signup,
    signup_groups,
)

urlpatterns = [
    path("auth/csrf/", csrf_token, name="auth-csrf"),
    path("auth/signup/", signup, name="auth-signup"),
    path("auth/login/", login_user, name="auth-login"),
    path("auth/logout/", logout_user, name="auth-logout"),
    path("auth/me/", current_user, name="auth-me"),
    path("groups/", signup_groups, name="signup-groups"),
    path(
        "me/scores/<slug:challenge_slug>/",
        save_challenge_score,
        name="save-challenge-score",
    ),
    path("<int:user_id>/profile/", user_profile, name="user-profile"),
    path("leaderboard/", leaderboard, name="leaderboard"),
    path("<slug:username>/", user_by_slug, name="user-detail"),
]
