from django.core.validators import MaxValueValidator
from django.db import models


class ChallengeAttempt(models.Model):
    submission_id = models.CharField(max_length=36, unique=True, editable=False)
    profile = models.ForeignKey(
        "users.UserProfile",
        on_delete=models.CASCADE,
        related_name="attempts",
    )
    challenge = models.ForeignKey(
        "challenges.Challenge",
        to_field="slug",
        db_column="challenge_slug",
        on_delete=models.CASCADE,
        related_name="attempts",
    )
    score = models.PositiveSmallIntegerField(validators=[MaxValueValidator(3)])
    completed_at = models.DateTimeField()
    received_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-completed_at", "-received_at"]
        db_table = "users_challengeattempt"

    def __str__(self):
        return f"{self.profile.user.username}: {self.challenge.name} ({self.score})"
