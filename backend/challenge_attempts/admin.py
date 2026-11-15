from django.contrib import admin

from .models import ChallengeAttempt


@admin.register(ChallengeAttempt)
class ChallengeAttemptAdmin(admin.ModelAdmin):
    list_display = ("profile", "challenge", "score", "completed_at", "received_at")
    list_filter = ("challenge", "completed_at")
    search_fields = ("profile__user__username", "challenge__name")
    readonly_fields = (
        "id",
        "submission_id",
        "profile",
        "challenge",
        "score",
        "completed_at",
        "received_at",
    )
    list_select_related = ("profile__user", "challenge")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
