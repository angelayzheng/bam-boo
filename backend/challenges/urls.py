from django.urls import path

from play.adapters.views import start_challenge

from .adapters.views import challenge_detail, challenge_list

urlpatterns = [
    path("", challenge_list, name="challenge-list"),
    path("<slug:slug>/attempts/", start_challenge, name="challenge-start-attempt"),
    path("<slug:slug>/", challenge_detail, name="challenge-detail"),
]
