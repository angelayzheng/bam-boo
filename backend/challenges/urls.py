from django.urls import path

from .views import challenge_detail, challenge_detail_by_slug, challenge_list

urlpatterns = [
    path("", challenge_list, name="challenge-list"),
    path("<int:challenge_id>/", challenge_detail, name="challenge-detail"),
    path("<slug:slug>/", challenge_detail_by_slug, name="challenge-detail-by-slug"),
]
