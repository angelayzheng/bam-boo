from django.contrib import admin

from tone.models import ToneVector


@admin.register(ToneVector)
class ToneVectorAdmin(admin.ModelAdmin):
    list_display = ("id", "word")
    search_fields = ("word",)
    readonly_fields = ("vector",)
