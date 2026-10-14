import tempfile
from pathlib import Path

from django.core.exceptions import ValidationError
from django.core.management import call_command
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


class SeedKaleDemoTests(TestCase):
    def _seed(self):
        media = tempfile.TemporaryDirectory()
        self.addCleanup(media.cleanup)
        with override_settings(MEDIA_ROOT=media.name):
            call_command("seed_kale_demo")
        return media

    def test_seed_creates_demo_challenge(self):
        media = self._seed()
        media_root = Path(media.name)
        challenge = Challenge.objects.get(slug="forgot-password-x3")
        self.assertEqual(challenge.name, "Forgot Password x3")
        self.assertEqual(challenge.tone, "frustrated")
        self.assertEqual(challenge.required_action, "reset password")
        self.assertEqual(challenge.difficulty, 1)
        self.assertEqual(challenge.category, "account")

        seen_files = []

        tree = challenge.conversation_tree
        self.assertEqual(tree["node_key"], "c1")
        self.assertEqual(tree["type"], "question")

        def _check(node, expected_type, depth=0):
            self.assertEqual(node["type"], expected_type)
            self.assertTrue(node["text_file"].endswith(".txt"))
            self.assertTrue(node["audio_file"].endswith(".mp3"))
            for key in ("text_file", "audio_file"):
                path = media_root / node[key]
                self.assertTrue(path.is_file(), f"Missing seeded file: {path}")
                self.assertGreater(path.stat().st_size, 0)
                seen_files.append(node[key])
            kinds = [child["type"] for child in node["children"]]
            self.assertTrue(
                all(kind != expected_type for kind in kinds),
                f"Layer below {node['node_key']} must alternate.",
            )
            for child in node["children"]:
                _check(
                    child,
                    "response" if expected_type == "question" else "question",
                    depth + 1,
                )

        _check(tree, "question")
        # 13 turns x (transcript + audio) = 26 referenced files.
        self.assertEqual(len(seen_files), 26)

        paths = []

        def _collect(node, path):
            path = [*path, node["node_key"]]
            if not node["children"]:
                paths.append(path)
            for child in node["children"]:
                _collect(child, path)

        _collect(tree, [])
        self.assertEqual(
            paths,
            [
                ["c1", "a1", "c2", "a4", "c5"],
                ["c1", "a2", "c3", "a5", "c6"],
                ["c1", "a3", "c4", "a6", "c7"],
            ],
        )

    def test_seed_is_idempotent(self):
        self._seed()
        with tempfile.TemporaryDirectory() as media:
            with override_settings(MEDIA_ROOT=media):
                call_command("seed_kale_demo")
        self.assertEqual(Challenge.objects.filter(slug="forgot-password-x3").count(), 1)

    def test_seeded_challenge_served_by_api(self):
        self._seed()
        challenge = Challenge.objects.get(slug="forgot-password-x3")
        response = self.client.get(f"/api/challenges/{challenge.id}/")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["category"], "account")
        tree = payload["conversation_tree"]
        self.assertEqual(tree["node_key"], "c1")
        # DB stores bare filename pairs; the API resolves them to URLs.
        self.assertTrue(tree["text_file"].endswith("c1.txt"))
        self.assertTrue(tree["transcript_url"].endswith(tree["text_file"]))
        self.assertTrue(tree["audio_url"].endswith(tree["audio_file"]))
        self.assertEqual(
            [child["node_key"] for child in tree["children"]], ["a1", "a2", "a3"]
        )
