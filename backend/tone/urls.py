from django.urls import path

from .views import tone_similarity

urlpatterns = [
    path("<slug:tone1>&<slug:tone2>/", tone_similarity, name="tone-similarity"),
]
