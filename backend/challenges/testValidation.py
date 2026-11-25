import json
import shutil
from copy import deepcopy
from io import StringIO
from unittest.mock import patch

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import override_settings

from . import package
from .importer import import_challenge_archive
from .models import Challenge
from .package import CHALLENGES_DIR
from .testSupport import (
    MediaTestCase,
    challenge_manifest,
    make_zip,
    make_zip_from_folder,
    write_package,
)


class ChallengeValidationTests(MediaTestCase):
    def create_challenge(self, slug="greeting", name=None, challenge_date=None):
        manifest = challenge_manifest(slug=slug)
        if name is not None:
            manifest["name"] = name
        source_folder = write_package(self.source, manifest)
        shutil.copytree(
            source_folder,
            self.media / "challenges" / slug,
        )
        loaded = package.load_challenge_package(source_folder)
        return Challenge.objects.create(
            name=loaded.metadata["name"],
            slug=loaded.slug,
            challenge_date=challenge_date or loaded.metadata["challenge_date"],
            difficulty=loaded.metadata["difficulty"],
            category=loaded.metadata["category"],
            tone=loaded.metadata["tone"],
            required_action=loaded.metadata["required_action"],
            conversation_tree=loaded.conversation_tree,
        )

    def run_validation(self):
        stdout = StringIO()
        stderr = StringIO()
        try:
            call_command("validate_challenges", stdout=stdout, stderr=stderr)
        except CommandError as error:
            return str(error), stdout.getvalue(), stderr.getvalue()
        return None, stdout.getvalue(), stderr.getvalue()

    def assert_validation_passes(self):
        message, stdout, stderr = self.run_validation()
        self.assertIsNone(message)
        self.assertEqual(stdout.strip(), "OK")
        self.assertEqual(stderr, "")

    def validation_errors(self):
        message, _, stderr = self.run_validation()
        self.assertEqual(message, "Challenge validation failed.")
        return [line.removeprefix("ERROR: ") for line in stderr.splitlines()]

    def test_clean_database_passes(self):
        self.create_challenge()
        self.assert_validation_passes()

    def test_missing_published_transcript_fails(self):
        challenge = self.create_challenge()
        transcript = self.media / challenge.conversation_tree["text_file"]
        transcript.unlink()
        errors = self.validation_errors()
        self.assertTrue(any("media file is missing" in error for error in errors))

    def test_missing_source_package_fails(self):
        self.create_challenge()
        shutil.rmtree(self.source / "greeting")
        errors = self.validation_errors()
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
        errors = self.validation_errors()
        self.assertTrue(
            any("source metadata 'name' differs" in error for error in errors)
        )

    def test_source_and_published_media_mismatch_fails(self):
        challenge = self.create_challenge()
        media_transcript = self.media / challenge.conversation_tree["text_file"]
        media_transcript.write_text("Changed transcript\n", encoding="utf-8")
        errors = self.validation_errors()
        self.assertTrue(
            any("source and published media differ" in error for error in errors)
        )

    def test_invalid_utf8_published_transcript_fails(self):
        challenge = self.create_challenge()
        media_transcript = self.media / challenge.conversation_tree["text_file"]
        media_transcript.write_bytes(b"invalid \x92 text")
        errors = self.validation_errors()
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
        errors = self.validation_errors()
        self.assertIn("empty: conversation tree is empty.", errors)

    def test_wrong_published_path_fails(self):
        challenge = self.create_challenge()
        tree = deepcopy(challenge.conversation_tree)
        tree["text_file"] = "challenges/greeting/other/q1.txt"
        challenge.conversation_tree = tree
        challenge.save()
        errors = self.validation_errors()
        self.assertTrue(any("stored path must be" in error for error in errors))

    @override_settings(ROOT_URLCONF="challenges.testUrls")
    def test_media_urls_are_retrievable(self):
        self.create_challenge()
        self.assert_validation_passes()

    def test_bundled_demo_imports_and_passes_validation(self):
        import_challenge_archive(
            make_zip_from_folder(CHALLENGES_DIR / "forgot-password-x3")
        )
        self.assert_validation_passes()

    def test_imported_string_difficulty_passes_validation(self):
        result = import_challenge_archive(make_zip(challenge_manifest(difficulty="1")))
        self.assertEqual(result.challenge.difficulty, 1)
        self.assert_validation_passes()

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

    def test_command_reports_invalid_challenge_row(self):
        challenge = self.create_challenge()
        Challenge.objects.filter(slug=challenge.slug).update(
            conversation_tree={"bad": True}
        )
        stdout = StringIO()
        stderr = StringIO()
        with self.assertRaises(CommandError) as error:
            call_command("validate_challenges", stdout=stdout, stderr=stderr)

        self.assertEqual(str(error.exception), "Challenge validation failed.")
        self.assertIn(f"{challenge.slug}: invalid challenge row:", stderr.getvalue())

    def test_command_reports_challenge_errors_in_slug_order(self):
        self.create_challenge(slug="zulu", name="Zulu Greeting")
        self.create_challenge(
            slug="alpha", name="Alpha Greeting", challenge_date="2026-10-16"
        )
        shutil.rmtree(self.media / "challenges" / "zulu")
        shutil.rmtree(self.media / "challenges" / "alpha")
        stdout = StringIO()
        stderr = StringIO()
        with self.assertRaises(CommandError):
            call_command("validate_challenges", stdout=stdout, stderr=stderr)

        errors = stderr.getvalue()
        self.assertLess(errors.index("alpha:"), errors.index("zulu:"))

    def test_command_reports_validator_failures(self):
        stdout = StringIO()
        stderr = StringIO()
        with patch(
            "challenges.adapters.challengeValidator.DjangoChallengeValidator.database_errors",
            side_effect=RuntimeError("boom"),
        ):
            with self.assertRaises(CommandError) as error:
                call_command("validate_challenges", stdout=stdout, stderr=stderr)

        self.assertEqual(str(error.exception), "Could not validate challenges: boom")
        self.assertEqual(stdout.getvalue(), "")
        self.assertEqual(stderr.getvalue(), "")

    def test_command_reports_container_failures(self):
        stdout = StringIO()
        stderr = StringIO()
        with patch(
            "challenges.management.commands.validate_challenges.get_container",
            side_effect=RuntimeError("boom"),
        ):
            with self.assertRaises(CommandError) as error:
                call_command("validate_challenges", stdout=stdout, stderr=stderr)

        self.assertEqual(str(error.exception), "Could not validate challenges: boom")
        self.assertEqual(stdout.getvalue(), "")
        self.assertEqual(stderr.getvalue(), "")
