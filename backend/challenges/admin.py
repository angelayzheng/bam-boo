from django.contrib import admin

from .models import Challenge


@admin.register(Challenge)
class ChallengeAdmin(admin.ModelAdmin):
    list_display = ("slug", "name", "category", "difficulty", "challenge_date")
    list_filter = ("category", "difficulty")
    search_fields = ("slug", "name", "tone")
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ("id",)
