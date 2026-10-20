from django.urls import path

from .views import challenge_detail, challenge_list

urlpatterns = [
    path("", challenge_list, name="challenge-list"),
    path("<int:challenge_id>/", challenge_detail, name="challenge-detail"),
]
