from django.urls import path

from .views import tone_similarity

urlpatterns = [
    path("<slug:challenge_slug>/", tone_similarity, name="tone-similarity"),
]
