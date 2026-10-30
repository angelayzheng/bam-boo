import io
import json
import stat
import tempfile
import zipfile
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch

from django.contrib.auth.models import Permission, User
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings
from django.urls import reverse

from .importer import (
    CHALLENGES_DIR,
    ChallengePackageError,
    import_challenge_archive,
)
from .models import Challenge, validate_conversation_tree

VALID_TREE = {
    "type": "question",
    "node_key": "q1",
    "text_file": "challenges/greeting/q1.txt",
    "audio_file": "challenges/greeting/q1.mp3",
    "children": [
        {
            "type": "response",
            "node_key": "r1",
            "text_file": "challenges/greeting/r1.txt",
            "audio_file": "challenges/greeting/r1.mp3",
            "children": [
                {
                    "type": "question",
                    "node_key": "q2",
                    "text_file": "challenges/greeting/q2.txt",
                    "audio_file": "challenges/greeting/q2.mp3",
                    "children": [],
                }
            ],
        }
    ],
}


def make_challenge(**kwargs):
    defaults = {
        "name": "Morning Greeting",
        "slug": "morning-greeting",
        "challenge_date": "2026-10-14",
        "difficulty": 2,
        "category": "social",
        "tone": "friendly",
        "required_action": "Greet the customer warmly.",
        "conversation_tree": VALID_TREE,
    }
    defaults.update(kwargs)
    return Challenge.objects.create(**defaults)


def _relative_tree():
    tree = deepcopy(VALID_TREE)

    def rewrite(node):
        key = node["node_key"]
        node["text_file"] = f"transcripts/{key}.txt"
        node["audio_file"] = f"audio/{key}.mp3"
        for child in node["children"]:
            rewrite(child)

    rewrite(tree)
    return tree


def _walk_tree(node):
    yield node
    for child in node["children"]:
        yield from _walk_tree(child)


def challenge_manifest(slug="greeting", **overrides):
    manifest = {
        "name": "Greeting",
        "slug": slug,
        "challenge_date": "2026-10-15",
        "difficulty": 1,
        "category": "social",
        "tone": "friendly",
        "required_action": "greet warmly",
        "conversation_tree": _relative_tree(),
    }
    manifest.update(overrides)
    return manifest


def make_zip(manifest=None, *, folder_name=None, extra_entries=None):
    manifest = manifest or challenge_manifest()
    folder_name = folder_name or manifest["slug"]
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(
            f"{folder_name}/{folder_name}.json",
            json.dumps(manifest),
        )
        for node in _walk_tree(manifest["conversation_tree"]):
            key = node["node_key"]
            archive.writestr(
                f"{folder_name}/transcripts/{key}.txt",
                f"Transcript for {key}\n",
            )
            archive.writestr(
                f"{folder_name}/audio/{key}.mp3",
                b"ID3 simulated audio",
            )
        for name, content in (extra_entries or {}).items():
            archive.writestr(name, content)
    return SimpleUploadedFile(
        "challenge.zip",
        buffer.getvalue(),
        content_type="application/zip",
    )


class MediaTestCase(TestCase):
    def setUp(self):
        super().setUp()
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.media = Path(temporary.name)
        settings_override = override_settings(MEDIA_ROOT=temporary.name)
        settings_override.enable()
        self.addCleanup(settings_override.disable)


class ConversationTreeValidatorTests(TestCase):
    def test_valid_tree_passes(self):
        validate_conversation_tree(VALID_TREE)

    def test_root_must_be_question(self):
        bad = {**VALID_TREE, "type": "response"}
        with self.assertRaises(ValidationError):
            validate_conversation_tree(bad)

    def test_layers_must_alternate(self):
        bad_child = {**VALID_TREE["children"][0], "type": "question"}
        bad = {**VALID_TREE, "children": [bad_child]}
        with self.assertRaises(ValidationError):
            validate_conversation_tree(bad)

    def test_audio_must_be_mp3(self):
        bad = {**VALID_TREE, "audio_file": "challenges/greeting/q1.wav"}
        with self.assertRaises(ValidationError):
            validate_conversation_tree(bad)

    def test_transcript_must_be_txt(self):
        bad = {**VALID_TREE, "text_file": "challenges/greeting/q1.md"}
        with self.assertRaises(ValidationError):
            validate_conversation_tree(bad)

    def test_absolute_paths_rejected(self):
        bad = {**VALID_TREE, "text_file": "/etc/q1.txt"}
        with self.assertRaises(ValidationError):
            validate_conversation_tree(bad)

    def test_duplicate_node_keys_rejected(self):
        child = {
            "type": "response",
            "node_key": "q1",
            "text_file": "challenges/greeting/r1.txt",
            "audio_file": "challenges/greeting/r1.mp3",
            "children": [],
        }
        bad = {**VALID_TREE, "children": [child]}
        with self.assertRaises(ValidationError):
            validate_conversation_tree(bad)


class ChallengeModelTests(TestCase):
    def test_slug_is_unique_and_stable_when_metadata_changes(self):
        challenge = make_challenge()
        self.assertEqual(challenge.slug, "morning-greeting")
        challenge.name = "Updated Greeting"
        challenge.challenge_date = "2026-10-20"
        challenge.save()
        challenge.refresh_from_db()
        self.assertEqual(challenge.slug, "morning-greeting")
        with self.assertRaises(ValidationError):
            make_challenge(name="Another Greeting", slug=challenge.slug)

    def test_multiple_challenges_can_share_a_date(self):
        first = make_challenge()
        second = make_challenge(name="Evening Greeting", slug="evening-greeting")
        self.assertNotEqual(first.slug, second.slug)

    def test_difficulty_bounds_enforced(self):
        with self.assertRaises(ValidationError):
            make_challenge(name="Too hard", slug="too-hard", difficulty=6)

    def test_challenge_list_and_detail_endpoints(self):
        challenge = make_challenge()
        listing = self.client.get("/api/challenges/")
        self.assertEqual(listing.status_code, 200)
        self.assertEqual(len(listing.json()["challenges"]), 1)

        detail = self.client.get(f"/api/challenges/{challenge.id}/")
        self.assertEqual(detail.status_code, 200)
        payload = detail.json()
        self.assertEqual(payload["slug"], "morning-greeting")
        self.assertEqual(payload["name"], "Morning Greeting")
        self.assertEqual(payload["required_action"], "Greet the customer warmly.")
        self.assertEqual(payload["conversation_tree"]["node_key"], "q1")

    def test_challenge_list_category_filter(self):
        make_challenge()
        make_challenge(
            name="Server Outage",
            slug="server-outage",
            category="emergency",
            difficulty=5,
        )
        filtered = self.client.get("/api/challenges/?category=emergency")
        self.assertEqual(len(filtered.json()["challenges"]), 1)
        self.assertEqual(filtered.json()["challenges"][0]["slug"], "server-outage")

    def test_challenge_detail_404(self):
        response = self.client.get("/api/challenges/9999/")
        self.assertEqual(response.status_code, 404)


class MissingChallengeSourceTests(TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.missing_source = Path(temporary.name) / "challenges"

    def test_import_reports_missing_challenge_source_directory(self):
        with patch(
            "challenges.management.commands.import_challenges.CHALLENGES_DIR",
            self.missing_source,
        ):
            with self.assertRaisesMessage(
                CommandError,
                f"Challenge source directory not found: {self.missing_source}",
            ):
                call_command("import_challenges")

    def test_seed_reports_missing_challenge_source_directory(self):
        for force in (False, True):
            with self.subTest(force=force):
                options = {"force": True} if force else {}
                with patch(
                    "challenges.management.commands.import_challenges.CHALLENGES_DIR",
                    self.missing_source,
                ):
                    with self.assertRaisesMessage(
                        CommandError,
                        f"Challenge source directory not found: {self.missing_source}",
                    ):
                        call_command("seed_kale_demo", **options)


class ImportChallengesTests(TestCase):
    def setUp(self):
        source = tempfile.TemporaryDirectory()
        media = tempfile.TemporaryDirectory()
        self.addCleanup(source.cleanup)
        self.addCleanup(media.cleanup)
        self.source = Path(source.name)
        self.media = Path(media.name)
        settings_override = override_settings(MEDIA_ROOT=media.name)
        settings_override.enable()
        self.addCleanup(settings_override.disable)
        source_override = patch(
            "challenges.management.commands.import_challenges.CHALLENGES_DIR",
            self.source,
        )
        source_override.start()
        self.addCleanup(source_override.stop)

    def _package(self, slug="greeting"):
        folder = self.source / slug
        tree = deepcopy(VALID_TREE)

        def create_files(node):
            key = node["node_key"]
            node["text_file"] = f"transcripts/{key}.txt"
            node["audio_file"] = f"audio/{key}.mp3"
            for field in ("text_file", "audio_file"):
                target = folder / node[field]
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes("Hello! Let’s begin.\n".encode("utf-8"))
            for child in node["children"]:
                create_files(child)

        create_files(tree)
        manifest = {
            "name": slug.title(),
            "slug": slug,
            "challenge_date": "2026-10-15",
            "difficulty": 1,
            "category": "social",
            "tone": "friendly",
            "required_action": "greet warmly",
            "conversation_tree": tree,
        }
        self._write_manifest(folder, manifest)
        return folder, manifest

    def _write_manifest(self, folder, manifest):
        (folder / f"{folder.name}.json").write_text(
            json.dumps(manifest), encoding="utf-8"
        )

    def test_imports_all_challenges_into_separate_local_directories(self):
        for slug in ("greeting", "farewell"):
            self._package(slug)
        call_command("import_challenges")
        self.assertEqual(Challenge.objects.count(), 2)
        for challenge in Challenge.objects.all():
            prefix = f"challenges/{challenge.slug}/"
            node = challenge.conversation_tree
            self.assertTrue(node["text_file"].startswith(prefix))
            self.assertTrue((self.media / node["audio_file"]).is_file())
            self.assertIn(
                "Let’s begin",
                (self.media / node["text_file"]).read_text(encoding="utf-8"),
            )
            self.assertTrue((self.media / prefix / f"{challenge.slug}.json").is_file())

    def test_selects_a_challenge_by_its_slug(self):
        _, first = self._package()
        self._package("farewell")
        call_command("import_challenges", first["slug"])
        self.assertEqual(
            list(Challenge.objects.values_list("slug", flat=True)),
            [first["slug"]],
        )

    def test_unknown_challenge_is_an_actionable_error(self):
        with self.assertRaisesMessage(CommandError, "Unknown challenge slugs"):
            call_command("import_challenges", "missing")

    def test_missing_file_prevents_any_selected_challenge_from_being_imported(self):
        self._package("first")
        folder, manifest = self._package("second")
        (folder / manifest["conversation_tree"]["audio_file"]).unlink()
        with self.assertRaisesMessage(CommandError, "Missing or empty file"):
            call_command("import_challenges")
        self.assertEqual(Challenge.objects.count(), 0)
        self.assertEqual(list(self.media.iterdir()), [])

    def test_transcripts_must_be_utf8(self):
        folder, manifest = self._package()
        (folder / manifest["conversation_tree"]["text_file"]).write_bytes(
            b"Let\x92s begin"
        )
        with self.assertRaisesMessage(CommandError, "Invalid challenge package"):
            call_command("import_challenges")

    def test_folder_and_manifest_slugs_must_match(self):
        folder, manifest = self._package()
        manifest["slug"] = "different-challenge"
        self._write_manifest(folder, manifest)
        with self.assertRaisesMessage(CommandError, "slug must match"):
            call_command("import_challenges")

    def test_windows_path_traversal_in_node_key_is_rejected(self):
        folder, manifest = self._package()
        node = manifest["conversation_tree"]
        node["node_key"] = "..\\outside"
        node["text_file"] = "transcripts/..\\outside.txt"
        node["audio_file"] = "audio/..\\outside.mp3"
        self._write_manifest(folder, manifest)
        with self.assertRaises(CommandError):
            call_command("import_challenges")

    def test_existing_challenges_are_skipped_until_replace_is_requested(self):
        folder, manifest = self._package()
        call_command("import_challenges")
        original = Challenge.objects.get()
        manifest["name"] = "Updated Greeting"
        self._write_manifest(folder, manifest)
        call_command("import_challenges")
        original.refresh_from_db()
        self.assertEqual(original.name, "Greeting")
        call_command("import_challenges", replace=True)
        updated = Challenge.objects.get()
        self.assertEqual(updated.pk, original.pk)
        self.assertEqual(updated.name, "Updated Greeting")
        self.assertEqual(updated.slug, original.slug)

    def test_duplicate_names_in_batch_are_rejected_before_installing(self):
        self._package("first")
        folder, manifest = self._package("second")
        manifest["name"] = "First"
        self._write_manifest(folder, manifest)
        with self.assertRaisesMessage(CommandError, "duplicate name"):
            call_command("import_challenges")
        self.assertEqual(Challenge.objects.count(), 0)

    def test_failed_replace_restores_published_files(self):
        folder, manifest = self._package()
        call_command("import_challenges")
        original = Challenge.objects.get()
        relative = manifest["conversation_tree"]["text_file"]
        original_text = (
            self.media / original.conversation_tree["text_file"]
        ).read_bytes()
        (folder / relative).write_text("Changed text", encoding="utf-8")
        with patch.object(
            Challenge, "save", side_effect=RuntimeError("Simulated failure")
        ):
            with self.assertRaisesMessage(RuntimeError, "Simulated failure"):
                call_command("import_challenges", replace=True)
        self.assertEqual(
            (self.media / original.conversation_tree["text_file"]).read_bytes(),
            original_text,
        )
        self.assertEqual(
            list((self.media / "challenges").iterdir()),
            [self.media / "challenges" / original.slug],
        )


class ChallengeArchiveImportTests(MediaTestCase):
    def test_imports_a_valid_zip(self):
        result = import_challenge_archive(make_zip())
        self.assertFalse(result.replaced)
        self.assertEqual(result.turn_count, 3)
        challenge = Challenge.objects.get(slug="greeting")
        self.assertEqual(challenge.name, "Greeting")
        self.assertTrue(
            (self.media / challenge.conversation_tree["audio_file"]).is_file()
        )
        self.assertTrue(
            (self.media / challenge.conversation_tree["text_file"]).is_file()
        )
        self.assertTrue(
            (self.media / "challenges" / "greeting" / "greeting.json").is_file()
        )

    def test_bundled_demo_package_is_importable(self):
        folder = CHALLENGES_DIR / "forgot-password-x3"
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
            for path in folder.rglob("*"):
                if path.is_file():
                    archive.write(
                        path,
                        f"{folder.name}/{path.relative_to(folder).as_posix()}",
                    )
        upload = SimpleUploadedFile(
            "challenge.zip",
            buffer.getvalue(),
            content_type="application/zip",
        )
        result = import_challenge_archive(upload)
        self.assertEqual(result.challenge.slug, "forgot-password-x3")
        self.assertEqual(result.turn_count, 13)

    def test_ignores_common_macos_metadata(self):
        upload = make_zip(
            extra_entries={
                "__MACOSX/._greeting": b"metadata",
                "._greeting": b"metadata",
                ".DS_Store": b"metadata",
            }
        )
        result = import_challenge_archive(upload)
        self.assertEqual(result.challenge.slug, "greeting")

    def test_existing_slug_requires_replace_and_preserves_id(self):
        first = import_challenge_archive(make_zip())
        with self.assertRaisesMessage(ChallengePackageError, "already exists"):
            import_challenge_archive(
                make_zip(challenge_manifest(name="Updated Greeting"))
            )
        second = import_challenge_archive(
            make_zip(challenge_manifest(name="Updated Greeting")),
            replace=True,
        )
        self.assertTrue(second.replaced)
        self.assertEqual(second.challenge.pk, first.challenge.pk)
        self.assertEqual(Challenge.objects.get().name, "Updated Greeting")

    def test_rejects_path_traversal(self):
        for entry in ("../evil.txt", "/evil.txt", "greeting\\..\\evil.txt"):
            with self.subTest(entry=entry):
                with self.assertRaises(ChallengePackageError):
                    import_challenge_archive(make_zip(extra_entries={entry: b"bad"}))

    def test_rejects_unsupported_file_type(self):
        with self.assertRaisesMessage(ChallengePackageError, "unsupported file type"):
            import_challenge_archive(
                make_zip(extra_entries={"greeting/run.sh": b"bad"})
            )

    def test_rejects_multiple_top_level_folders(self):
        with self.assertRaisesMessage(ChallengePackageError, "exactly one top-level"):
            import_challenge_archive(
                make_zip(extra_entries={"other/readme.txt": b"other"})
            )

    def test_rejects_folder_name_that_does_not_match_slug(self):
        with self.assertRaisesMessage(ChallengePackageError, "slug must match"):
            import_challenge_archive(make_zip(folder_name="wrong-name"))

    def test_rejects_invalid_zip(self):
        upload = SimpleUploadedFile(
            "challenge.zip",
            b"not a zip",
            content_type="application/zip",
        )
        with self.assertRaisesMessage(ChallengePackageError, "valid .zip"):
            import_challenge_archive(upload)

    def test_rejects_symbolic_links(self):
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as archive:
            info = zipfile.ZipInfo("greeting/link")
            info.external_attr = (stat.S_IFLNK | 0o777) << 16
            archive.writestr(info, "target")
        upload = SimpleUploadedFile(
            "challenge.zip",
            buffer.getvalue(),
            content_type="application/zip",
        )
        with self.assertRaisesMessage(ChallengePackageError, "symbolic link"):
            import_challenge_archive(upload)

    def test_enforces_file_count_limit(self):
        with override_settings(CHALLENGE_IMPORT_MAX_FILES=1):
            with self.assertRaisesMessage(ChallengePackageError, "more than 1 files"):
                import_challenge_archive(make_zip())

    def test_enforces_archive_size_limit(self):
        with override_settings(CHALLENGE_IMPORT_MAX_ARCHIVE_BYTES=10):
            with self.assertRaisesMessage(ChallengePackageError, "MB or smaller"):
                import_challenge_archive(make_zip())

    def test_enforces_uncompressed_size_limit(self):
        with override_settings(CHALLENGE_IMPORT_MAX_UNCOMPRESSED_BYTES=10):
            with self.assertRaisesMessage(ChallengePackageError, "expands beyond"):
                import_challenge_archive(make_zip())


class ChallengeAdminImportTests(MediaTestCase):
    def setUp(self):
        super().setUp()
        self.publisher = User.objects.create_user(
            "publisher",
            password="password",
            is_staff=True,
        )
        self.publisher.user_permissions.set(
            Permission.objects.filter(
                content_type__app_label="challenges",
                codename__in=(
                    "add_challenge",
                    "change_challenge",
                    "view_challenge",
                ),
            )
        )
        self.client.force_login(self.publisher)
        self.url = reverse("admin:challenges_challenge_import_package")

    def test_import_page_is_available_to_publishers(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Import challenge package")

    def test_challenge_list_links_to_import_for_publishers(self):
        response = self.client.get(reverse("admin:challenges_challenge_changelist"))
        self.assertContains(response, self.url)

    def test_import_page_requires_challenge_permissions(self):
        viewer = User.objects.create_user(
            "viewer",
            password="password",
            is_staff=True,
        )
        self.client.force_login(viewer)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_valid_upload_imports_challenge(self):
        response = self.client.post(self.url, {"package": make_zip()})
        self.assertRedirects(
            response,
            reverse("admin:challenges_challenge_changelist"),
        )
        challenge = Challenge.objects.get(slug="greeting")
        self.assertEqual(challenge.name, "Greeting")
        self.assertTrue(
            (self.media / "challenges" / "greeting" / "greeting.json").is_file()
        )

    def test_invalid_upload_shows_error_and_changes_nothing(self):
        upload = SimpleUploadedFile(
            "challenge.zip",
            b"not a zip",
            content_type="application/zip",
        )
        response = self.client.post(self.url, {"package": upload})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "valid .zip")
        self.assertEqual(Challenge.objects.count(), 0)

    def test_existing_slug_requires_replace(self):
        self.client.post(self.url, {"package": make_zip()})
        response = self.client.post(
            self.url,
            {"package": make_zip(challenge_manifest(name="Changed Greeting"))},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "already exists")
        self.assertEqual(Challenge.objects.get().name, "Greeting")

        response = self.client.post(
            self.url,
            {
                "package": make_zip(challenge_manifest(name="Changed Greeting")),
                "replace": "on",
            },
        )
        self.assertRedirects(
            response,
            reverse("admin:challenges_challenge_changelist"),
        )
        self.assertEqual(Challenge.objects.get().name, "Changed Greeting")

    def test_change_form_keeps_slug_and_tree_read_only(self):
        challenge = make_challenge()
        response = self.client.get(
            reverse(
                "admin:challenges_challenge_change",
                args=[challenge.pk],
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'name="slug"')
        self.assertNotContains(response, 'name="conversation_tree"')

    def test_default_add_form_is_disabled(self):
        response = self.client.get(reverse("admin:challenges_challenge_add"))
        self.assertEqual(response.status_code, 403)
