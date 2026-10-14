from django.contrib import admin

from .models import Challenge


@admin.register(Challenge)
class ChallengeAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "difficulty", "tone", "challenge_date")
    list_filter = ("category", "difficulty")
    search_fields = ("name", "tone")
    prepopulated_fields = {"slug": ("name",)}
