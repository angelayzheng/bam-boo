import json
import shutil
from copy import deepcopy
from io import StringIO

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import override_settings

from . import package
from .importer import import_challenge_archive
from .models import Challenge
from .package import CHALLENGES_DIR
from .test_support import (
    MediaTestCase,
    challenge_manifest,
    make_zip_from_folder,
    write_package,
)
from .validation import ChallengeDatabaseValidator


class ChallengeValidationTests(MediaTestCase):
    def create_challenge(self, slug="greeting"):
        manifest = challenge_manifest(slug=slug)
        source_folder = write_package(self.source, manifest)
        shutil.copytree(
            source_folder,
            self.media / "challenges" / slug,
        )
        loaded = package.load_challenge_package(source_folder)
        return Challenge.objects.create(
            name=loaded.metadata["name"],
            slug=loaded.slug,
            challenge_date=loaded.metadata["challenge_date"],
            difficulty=loaded.metadata["difficulty"],
            category=loaded.metadata["category"],
            tone=loaded.metadata["tone"],
            required_action=loaded.metadata["required_action"],
            conversation_tree=loaded.conversation_tree,
        )

    def test_clean_database_passes(self):
        self.create_challenge()
        self.assertEqual(ChallengeDatabaseValidator().validate(), [])

    def test_missing_published_transcript_fails(self):
        challenge = self.create_challenge()
        transcript = self.media / challenge.conversation_tree["text_file"]
        transcript.unlink()
        errors = ChallengeDatabaseValidator().validate()
        self.assertTrue(any("media file is missing" in error for error in errors))

    def test_missing_source_package_fails(self):
        self.create_challenge()
        shutil.rmtree(self.source / "greeting")
        errors = ChallengeDatabaseValidator().validate()
        self.assertTrue(
            any("source package folder is missing" in error for error in errors)
        )

    def test_source_metadata_drift_fails(self):
        self.create_challenge()
        manifest = challenge_manifest(name="Changed Greeting")
        (self.source / "greeting" / "greeting.json").write_text(
            json.dumps(manifest),
            encoding="utf-8",
        )
        errors = ChallengeDatabaseValidator().validate()
        self.assertTrue(
            any("source metadata 'name' differs" in error for error in errors)
        )

    def test_source_and_published_media_mismatch_fails(self):
        challenge = self.create_challenge()
        media_transcript = self.media / challenge.conversation_tree["text_file"]
        media_transcript.write_text("Changed transcript\n", encoding="utf-8")
        errors = ChallengeDatabaseValidator().validate()
        self.assertTrue(
            any("source and published media differ" in error for error in errors)
        )

    def test_invalid_utf8_published_transcript_fails(self):
        challenge = self.create_challenge()
        media_transcript = self.media / challenge.conversation_tree["text_file"]
        media_transcript.write_bytes(b"invalid \x92 text")
        errors = ChallengeDatabaseValidator().validate()
        self.assertTrue(
            any("transcript is not valid UTF-8" in error for error in errors)
        )

    def test_empty_conversation_tree_fails(self):
        Challenge.objects.create(
            name="Empty Challenge",
            slug="empty",
            challenge_date="2026-10-15",
            difficulty=1,
            category="social",
            tone="friendly",
            required_action="do nothing",
            conversation_tree={},
        )
        errors = ChallengeDatabaseValidator().validate()
        self.assertIn("empty: conversation tree is empty.", errors)

    def test_wrong_published_path_fails(self):
        challenge = self.create_challenge()
        tree = deepcopy(challenge.conversation_tree)
        tree["text_file"] = "challenges/greeting/other/q1.txt"
        challenge.conversation_tree = tree
        challenge.save()
        errors = ChallengeDatabaseValidator().validate()
        self.assertTrue(any("stored path must be" in error for error in errors))

    @override_settings(ROOT_URLCONF="challenges.test_urls")
    def test_media_urls_are_retrievable(self):
        self.create_challenge()
        self.assertEqual(ChallengeDatabaseValidator().validate(), [])

    def test_bundled_demo_imports_and_passes_validation(self):
        import_challenge_archive(
            make_zip_from_folder(CHALLENGES_DIR / "forgot-password-x3")
        )
        self.assertEqual(ChallengeDatabaseValidator().validate(), [])

    def test_command_prints_ok(self):
        self.create_challenge()
        stdout = StringIO()
        call_command("validate_challenges", stdout=stdout)
        self.assertEqual(stdout.getvalue().strip(), "OK")

    def test_command_reports_errors_and_fails(self):
        challenge = self.create_challenge()
        (self.media / challenge.conversation_tree["audio_file"]).unlink()
        stdout = StringIO()
        stderr = StringIO()
        with self.assertRaises(CommandError):
            call_command(
                "validate_challenges",
                stdout=stdout,
                stderr=stderr,
            )
        self.assertEqual(stdout.getvalue(), "")
        self.assertIn("ERROR:", stderr.getvalue())
