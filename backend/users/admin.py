from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

from .models import ChallengeAttempt, UserProfile


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    fields = ("group", "avatar", "scores", "total_score", "login_days")
    readonly_fields = ("total_score",)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "group", "avatar", "total_score", "updated_at")
    list_filter = ("group", "avatar")
    list_select_related = ("user", "group")
    search_fields = ("user__username", "user__email")


class UserWithProfileAdmin(BaseUserAdmin):
    inlines = [UserProfileInline]


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


admin.site.unregister(User)
admin.site.register(User, UserWithProfileAdmin)
