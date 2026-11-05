from django.urls import path

from .views import challenge_detail, challenge_list

urlpatterns = [
    path("", challenge_list, name="challenge-list"),
    path("<slug:slug>/", challenge_detail, name="challenge-detail"),
]
