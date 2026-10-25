from django.urls import path

from .views import leaderboard, user_by_slug, user_profile

urlpatterns = [
    path("<int:user_id>/profile/", user_profile, name="user-profile"),
    path("leaderboard/", leaderboard, name="leaderboard"),
    path("<slug:username>/", user_by_slug, name="user-detail"),
]
