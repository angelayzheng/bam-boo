import json

from django import forms
from django.conf import settings
from django.contrib import admin, messages
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.urls import path
from django.utils.html import format_html

from config.container import get_container

from .adapters.archives import DEFAULT_MAX_ARCHIVE_BYTES
from .models import Challenge


class ChallengePackageImportForm(forms.Form):
    package = forms.FileField(
        label="Challenge package (.zip)",
        help_text=(
            "ZIP containing one <slug>/ folder with <slug>.json, audio/, "
            "and transcripts/."
        ),
    )
    replace = forms.BooleanField(
        required=False,
        label="Replace an existing challenge with this slug",
        help_text="Tick this only when updating a challenge that is already imported.",
    )

    def clean_package(self):
        package = self.cleaned_data["package"]
        if not package.name.lower().endswith(".zip"):
            raise forms.ValidationError("Upload a .zip file.")
        max_bytes = getattr(
            settings,
            "CHALLENGE_IMPORT_MAX_ARCHIVE_BYTES",
            DEFAULT_MAX_ARCHIVE_BYTES,
        )
        if (package.size or 0) > max_bytes:
            raise forms.ValidationError(
                f"The ZIP must be {max_bytes // (1024 * 1024)} MB or smaller."
            )
        return package


@admin.register(Challenge)
class ChallengeAdmin(admin.ModelAdmin):
    list_display = ("slug", "name", "category", "difficulty", "challenge_date")
    list_filter = ("category", "difficulty")
    search_fields = ("slug", "name", "tone")
    fields = (
        "id",
        "name",
        "slug",
        "challenge_date",
        "difficulty",
        "category",
        "tone",
        "required_action",
        "conversation_tree_display",
    )
    readonly_fields = (
        "id",
        "name",
        "slug",
        "challenge_date",
        "difficulty",
        "category",
        "tone",
        "required_action",
        "conversation_tree_display",
    )

    @admin.display(description="Conversation tree")
    def conversation_tree_display(self, obj):
        if not obj.conversation_tree:
            return "No conversation tree."
        return format_html(
            "<pre>{}</pre>",
            json.dumps(obj.conversation_tree, indent=2, ensure_ascii=False),
        )

    def has_add_permission(self, request):
        return False

    def get_urls(self):
        return [
            path(
                "import-package/",
                self.admin_site.admin_view(self.import_package_view),
                name="challenges_challenge_import_package",
            ),
        ] + super().get_urls()

    def import_package_view(self, request):
        if not (
            request.user.has_perm("challenges.add_challenge")
            and request.user.has_perm("challenges.change_challenge")
        ):
            raise PermissionDenied

        form = ChallengePackageImportForm()
        if request.method == "POST":
            form = ChallengePackageImportForm(request.POST, request.FILES)
            if form.is_valid():
                use_case = get_container().build_import_challenge_package_use_case()
                use_case.controller.execute(
                    sources=[form.cleaned_data["package"]],
                    replace=form.cleaned_data["replace"],
                )
                view_model = use_case.presenter.view_model
                if not view_model.success:
                    form.add_error(None, view_model.message)
                else:
                    result = view_model.results[0]
                    challenge = Challenge.objects.get(slug=result.slug)
                    if result.replaced:
                        self.log_change(
                            request,
                            challenge,
                            "Replaced from an uploaded ZIP package.",
                        )
                    else:
                        self.log_addition(
                            request,
                            challenge,
                            "Imported from an uploaded ZIP package.",
                        )
                    self.message_user(
                        request,
                        view_model.message,
                        level=messages.SUCCESS,
                    )
                    return redirect("admin:challenges_challenge_changelist")

        context = {
            **self.admin_site.each_context(request),
            "title": "Import challenge package",
            "opts": self.model._meta,
            "form": form,
            "media": self.media + form.media,
        }
        return TemplateResponse(
            request,
            "admin/challenges/challenge/import_package.html",
            context,
        )
