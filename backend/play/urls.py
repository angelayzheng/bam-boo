from django.urls import path

from play.adapters.views import (
    choose_response,
    continue_conversation,
    get_run,
    submit_action,
    submit_tone,
)

urlpatterns = [
    path("<uuid:attempt_id>/", get_run, name="attempt-detail"),
    path("<uuid:attempt_id>/tone/", submit_tone, name="attempt-tone"),
    path("<uuid:attempt_id>/choices/", choose_response, name="attempt-choices"),
    path("<uuid:attempt_id>/continue/", continue_conversation, name="attempt-continue"),
    path("<uuid:attempt_id>/action/", submit_action, name="attempt-action"),
]
