from django.contrib import admin

from .models import Challenge


@admin.register(Challenge)
class ChallengeAdmin(admin.ModelAdmin):
    list_display = ("level_id", "name", "category", "difficulty", "challenge_date")
    list_filter = ("category", "difficulty")
    search_fields = ("level_id", "name", "tone")
    readonly_fields = ("level_id",)
    prepopulated_fields = {"slug": ("name",)}
