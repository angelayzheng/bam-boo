from django.urls import path

from .views import save_challenge_score

urlpatterns = [
    path("scores/<slug:challenge_slug>/", save_challenge_score, name="save-challenge-score"),
]
