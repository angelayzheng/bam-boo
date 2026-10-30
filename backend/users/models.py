from datetime import date

from django.contrib.auth.models import Group, User
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


class AvatarChoices(models.TextChoices):
    FOX = "fox", "Fox"
    OWL = "owl", "Owl"
    BEAR = "bear", "Bear"
    CAT = "cat", "Cat"
    ROBOT = "robot", "Robot"
    GHOST = "ghost", "Ghost"


def validate_scores(value):
    if not isinstance(value, dict):
        raise ValidationError("Scores must be a JSON object.")
    for key, score in value.items():
        if not isinstance(key, str) or not key.strip():
            raise ValidationError("Score keys must be non-empty strings.")
        if isinstance(score, bool) or not isinstance(score, int):
            raise ValidationError(f"Score for {key!r} must be a whole number.")
        if not 0 <= score <= 3:
            raise ValidationError(f"Score for {key!r} must be between 0 and 3.")


def validate_login_days(value):
    if not isinstance(value, list):
        raise ValidationError("Login days must be a JSON list.")
    seen = set()
    for entry in value:
        if not isinstance(entry, str):
            raise ValidationError("Each login day must be a YYYY-MM-DD string.")
        try:
            date.fromisoformat(entry)
        except ValueError as exc:
            raise ValidationError(
                f"Invalid login day {entry!r}; expected YYYY-MM-DD."
            ) from exc
        if entry in seen:
            raise ValidationError(f"Duplicate login day: {entry!r}.")
        seen.add(entry)


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    group = models.ForeignKey(
        Group, on_delete=models.SET_NULL, null=True, blank=True, related_name="profiles"
    )
    avatar = models.CharField(
        max_length=16, choices=AvatarChoices.choices, default=AvatarChoices.FOX
    )
    scores = models.JSONField(default=dict, blank=True, validators=[validate_scores])
    total_score = models.PositiveIntegerField(default=0)
    login_days = models.JSONField(
        default=list, blank=True, validators=[validate_login_days]
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-total_score"]

    def __str__(self):
        return f"Profile of {self.user.username}"

    def clean(self):
        super().clean()
        validate_scores(self.scores)
        validate_login_days(self.login_days)

    def recalculate_total(self):
        self.total_score = sum(self.scores.values())

    def add_score(self, challenge_id, score):
        if isinstance(score, bool) or not isinstance(score, int) or not 0 <= score <= 3:
            raise ValidationError("Score must be a whole number between 0 and 3.")
        self.scores[str(challenge_id)] = score
        self.recalculate_total()

    def record_login(self, day=None):
        day_str = (day or date.today()).isoformat()
        if day_str not in self.login_days:
            self.login_days = sorted([*self.login_days, day_str])

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class ChallengeAttempt(models.Model):
    submission_id = models.CharField(max_length=36, unique=True, editable=False)
    profile = models.ForeignKey(
        UserProfile, on_delete=models.CASCADE, related_name="attempts"
    )
    challenge = models.ForeignKey(
        "challenges.Challenge",
        on_delete=models.CASCADE,
        related_name="attempts",
    )
    score = models.PositiveSmallIntegerField(validators=[MaxValueValidator(3)])
    completed_at = models.DateTimeField()
    received_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-completed_at", "-received_at"]

    def __str__(self):
        return f"{self.profile.user.username}: {self.challenge.name} ({self.score})"


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
