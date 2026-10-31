from django.urls import path

from .views import tone_similarity

urlpatterns = [
    path("<int:challenge_id>/", tone_similarity, name="tone-similarity"),
]
