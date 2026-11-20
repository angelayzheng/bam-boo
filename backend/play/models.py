from uuid import uuid4

from django.conf import settings
from django.db import models


class ChallengeRun(models.Model):
    STAGES = [
        (stage, stage) for stage in ("tone", "conversation", "action", "completed")
    ]

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    challenge = models.ForeignKey(
        "challenges.Challenge", to_field="slug", on_delete=models.CASCADE
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL
    )
    stage = models.CharField(max_length=16, choices=STAGES, default="tone")
    conversation = models.JSONField(default=list)
    current_node = models.CharField(max_length=120, blank=True)
    tone_correct = models.BooleanField(null=True)
    tone_time = models.FloatField(null=True)
    tone_similarity = models.FloatField(null=True)
    action_correct = models.BooleanField(null=True)
    score = models.PositiveSmallIntegerField(null=True)
    completed_at = models.DateTimeField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = "play"
