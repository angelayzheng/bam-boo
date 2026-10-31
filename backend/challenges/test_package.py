import json
import tempfile
from pathlib import Path

from django.test import SimpleTestCase

from .package import (
    ChallengePackageError,
    iter_conversation_nodes,
    load_challenge_package,
)
from .test_support import challenge_manifest, write_package


class ChallengePackageTests(SimpleTestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)

    def test_loads_and_normalizes_a_package(self):
        source_folder = write_package(self.root, challenge_manifest())
        loaded = load_challenge_package(source_folder)
        self.assertEqual(loaded.slug, "greeting")
        self.assertEqual(loaded.turn_count, 3)
        self.assertEqual(
            loaded.conversation_tree["text_file"],
            "challenges/greeting/transcripts/q1.txt",
        )
        self.assertIn("audio/q1.mp3", loaded.files)
        self.assertIn("transcripts/q1.txt", loaded.files)

    def test_iterates_every_node(self):
        source_folder = write_package(self.root, challenge_manifest())
        loaded = load_challenge_package(source_folder)
        self.assertEqual(
            [
                node["node_key"]
                for node in iter_conversation_nodes(loaded.conversation_tree)
            ],
            ["q1", "r1", "q2"],
        )

    def test_reports_a_missing_media_file(self):
        source_folder = write_package(self.root, challenge_manifest())
        (source_folder / "audio" / "q1.mp3").unlink()
        with self.assertRaisesMessage(ChallengePackageError, "Missing or empty file"):
            load_challenge_package(source_folder)

    def test_reports_invalid_utf8_transcript(self):
        source_folder = write_package(self.root, challenge_manifest())
        (source_folder / "transcripts" / "q1.txt").write_bytes(b"invalid \x92 text")
        with self.assertRaisesMessage(
            ChallengePackageError, "Invalid challenge package"
        ):
            load_challenge_package(source_folder)

    def test_reports_missing_manifest(self):
        source_folder = write_package(self.root, challenge_manifest())
        (source_folder / "greeting.json").unlink()
        with self.assertRaisesMessage(
            ChallengePackageError, "Invalid challenge package"
        ):
            load_challenge_package(source_folder)

    def test_rejects_folder_and_manifest_slug_mismatch(self):
        manifest = challenge_manifest()
        source_folder = self.root / "other"
        write_package(self.root, manifest)
        source_folder.mkdir(parents=True, exist_ok=True)
        (source_folder / "other.json").write_text(
            json.dumps(manifest),
            encoding="utf-8",
        )
        with self.assertRaisesMessage(ChallengePackageError, "slug must match"):
            load_challenge_package(source_folder)
