import json
import tempfile
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings

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
    def test_level_id_is_unique_and_stable_when_metadata_changes(self):
        challenge = make_challenge()
        self.assertEqual(challenge.level_id, "2026-10-14-morning-greeting")
        challenge.name = "Updated Greeting"
        challenge.challenge_date = "2026-10-20"
        challenge.save()
        challenge.refresh_from_db()
        self.assertEqual(challenge.level_id, "2026-10-14-morning-greeting")
        with self.assertRaises(ValidationError):
            make_challenge(
                name="Another Greeting",
                slug="another-greeting",
                level_id=challenge.level_id,
            )

    def test_multiple_levels_can_share_a_date(self):
        first = make_challenge()
        second = make_challenge(name="Evening Greeting", slug="evening-greeting")
        self.assertNotEqual(first.level_id, second.level_id)

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
        self.assertEqual(payload["level_id"], "2026-10-14-morning-greeting")
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


class MissingLevelSourceTests(TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.missing_source = Path(temporary.name) / "levels"

    def test_import_reports_missing_level_source_directory(self):
        with patch(
            "challenges.management.commands.import_levels.LEVELS_DIR",
            self.missing_source,
        ):
            with self.assertRaisesMessage(
                CommandError,
                f"Level source directory not found: {self.missing_source}",
            ):
                call_command("import_levels")

    def test_seed_reports_missing_level_source_directory(self):
        for force in (False, True):
            with self.subTest(force=force):
                options = {"force": True} if force else {}
                with patch(
                    "challenges.management.commands.import_levels.LEVELS_DIR",
                    self.missing_source,
                ):
                    with self.assertRaisesMessage(
                        CommandError,
                        f"Level source directory not found: {self.missing_source}",
                    ):
                        call_command("seed_kale_demo", **options)


class ImportLevelsTests(TestCase):
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
            "challenges.management.commands.import_levels.LEVELS_DIR", self.source
        )
        source_override.start()
        self.addCleanup(source_override.stop)

    def _package(self, slug="greeting"):
        level_id = f"2026-10-15-{slug}"
        folder = self.source / level_id
        tree = deepcopy(VALID_TREE)

        def create_files(node):
            speaker = "customer" if node["type"] == "question" else "agent"
            key = node["node_key"]
            node["text_file"] = f"transcripts/{speaker}/{key}.txt"
            node["audio_file"] = f"audio/{speaker}/{key}.mp3"
            for field in ("text_file", "audio_file"):
                target = folder / node[field]
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes("Hello! Let’s begin.\n".encode("utf-8"))
            for child in node["children"]:
                create_files(child)

        create_files(tree)
        manifest = {
            "level_id": level_id,
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
        (folder / "level.json").write_text(json.dumps(manifest), encoding="utf-8")

    def test_imports_all_levels_into_separate_local_directories(self):
        for slug in ("greeting", "farewell"):
            self._package(slug)
        call_command("import_levels")
        self.assertEqual(Challenge.objects.count(), 2)
        for challenge in Challenge.objects.all():
            prefix = f"levels/{challenge.level_id}/"
            node = challenge.conversation_tree
            self.assertTrue(node["text_file"].startswith(prefix))
            self.assertTrue((self.media / node["audio_file"]).is_file())
            self.assertIn(
                "Let’s begin",
                (self.media / node["text_file"]).read_text(encoding="utf-8"),
            )
            self.assertTrue((self.media / prefix / "level.json").is_file())

    def test_selects_a_level_by_its_stable_id(self):
        _, first = self._package()
        self._package("farewell")
        call_command("import_levels", first["level_id"])
        self.assertEqual(
            list(Challenge.objects.values_list("level_id", flat=True)),
            [first["level_id"]],
        )

    def test_unknown_level_is_an_actionable_error(self):
        with self.assertRaisesMessage(CommandError, "Unknown level IDs"):
            call_command("import_levels", "missing")

    def test_missing_file_prevents_any_selected_level_from_being_imported(self):
        self._package("first")
        folder, manifest = self._package("second")
        (folder / manifest["conversation_tree"]["audio_file"]).unlink()
        with self.assertRaisesMessage(CommandError, "Missing or empty file"):
            call_command("import_levels")
        self.assertEqual(Challenge.objects.count(), 0)
        self.assertEqual(list(self.media.iterdir()), [])

    def test_transcripts_must_be_utf8(self):
        folder, manifest = self._package()
        (folder / manifest["conversation_tree"]["text_file"]).write_bytes(
            b"Let\x92s begin"
        )
        with self.assertRaisesMessage(CommandError, "Invalid level package"):
            call_command("import_levels")

    def test_folder_and_manifest_ids_must_match(self):
        folder, manifest = self._package()
        manifest["level_id"] = "different-level"
        self._write_manifest(folder, manifest)
        with self.assertRaisesMessage(CommandError, "level_id must match"):
            call_command("import_levels")

    def test_windows_path_traversal_in_node_key_is_rejected(self):
        folder, manifest = self._package()
        node = manifest["conversation_tree"]
        node["node_key"] = "..\\outside"
        node["text_file"] = "transcripts/customer/..\\outside.txt"
        node["audio_file"] = "audio/customer/..\\outside.mp3"
        self._write_manifest(folder, manifest)
        with self.assertRaises(CommandError):
            call_command("import_levels")

    def test_existing_levels_are_skipped_until_replace_is_requested(self):
        folder, manifest = self._package()
        call_command("import_levels")
        original = Challenge.objects.get()
        manifest["name"] = "Updated Greeting"
        self._write_manifest(folder, manifest)
        call_command("import_levels")
        original.refresh_from_db()
        self.assertEqual(original.name, "Greeting")
        call_command("import_levels", replace=True)
        updated = Challenge.objects.get()
        self.assertEqual(updated.pk, original.pk)
        self.assertEqual(updated.name, "Updated Greeting")
        self.assertEqual(updated.level_id, original.level_id)

    def test_duplicate_names_in_batch_are_rejected_before_installing(self):
        self._package("first")
        folder, manifest = self._package("second")
        manifest["name"] = "First"
        self._write_manifest(folder, manifest)
        with self.assertRaisesMessage(CommandError, "duplicate name"):
            call_command("import_levels")
        self.assertEqual(Challenge.objects.count(), 0)

    def test_failed_replace_restores_published_files(self):
        folder, manifest = self._package()
        call_command("import_levels")
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
                call_command("import_levels", replace=True)
        self.assertEqual(
            (self.media / original.conversation_tree["text_file"]).read_bytes(),
            original_text,
        )
        self.assertEqual(
            list((self.media / "levels").iterdir()),
            [self.media / "levels" / original.level_id],
        )
