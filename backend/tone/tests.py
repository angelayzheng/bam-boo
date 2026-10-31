import gzip
import sys
import tempfile
from array import array
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from tone.management.commands.load_vectors import Command, _vector_bytes
from tone.models import ToneVector
from challenges.models import Challenge

# A tiny three-word, two-dimension dataset that exercises the full load path
# without needing the real 300-dimension Numberbatch file.
SAMPLE_VECTORS = (
    ("cat", ["0.1", "-0.2"]),
    ("dog", ["0.3", "0.4"]),
    ("bird", ["-0.5", "0.6"]),
)


def _write_vectors_gz(path, vectors=SAMPLE_VECTORS, *, dimension=2, header_count=None):
    """Write a minimal Numberbatch-format gzip file."""
    count = header_count if header_count is not None else len(vectors)
    with gzip.open(path, "wt", encoding="utf-8") as fh:
        fh.write(f"{count} {dimension}\n")
        for word, values in vectors:
            fh.write(f"{word} {' '.join(values)}\n")


class ToneVectorModelTests(TestCase):
    def test_create_and_retrieve(self):
        blob = _vector_bytes(["0.1", "-0.2"])
        tv = ToneVector.objects.create(word="hello", vector=blob)
        tv.refresh_from_db()
        self.assertEqual(tv.word, "hello")
        self.assertIsInstance(tv.vector, (bytes, memoryview))

    def test_str_returns_word(self):
        tv = ToneVector(word="goodbye")
        self.assertEqual(str(tv), "goodbye")

    def test_word_is_unique(self):
        ToneVector.objects.create(word="unique", vector=b"\x00")
        with self.assertRaises(Exception):
            ToneVector.objects.create(word="unique", vector=b"\x01")


class VectorBytesTests(TestCase):
    def test_round_trip(self):
        values = ["1.5", "-2.0", "0.0"]
        blob = _vector_bytes(values)
        restored = array("f")
        restored.frombytes(blob)
        if sys.byteorder != "little":
            restored.byteswap()
        self.assertEqual(len(restored), 3)
        self.assertAlmostEqual(restored[0], 1.5, places=5)
        self.assertAlmostEqual(restored[1], -2.0, places=5)
        self.assertAlmostEqual(restored[2], 0.0, places=5)

    def test_output_is_bytes(self):
        self.assertIsInstance(_vector_bytes(["0.0"]), bytes)


class LoadVectorsCommandTests(TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmpdir.cleanup)
        self.data_file = Path(self.tmpdir.name) / "vectors.txt.gz"

    def _load(self, **kwargs):
        out = StringIO()
        err = StringIO()
        kwargs.setdefault("file", str(self.data_file))
        call_command("load_vectors", stdout=out, stderr=err, **kwargs)
        return out.getvalue(), err.getvalue()

    def test_loads_all_vectors(self):
        _write_vectors_gz(self.data_file)
        out, _ = self._load()
        self.assertEqual(ToneVector.objects.count(), 3)
        self.assertIn("3", out)
        for word, values in SAMPLE_VECTORS:
            tv = ToneVector.objects.get(word=word)
            restored = array("f")
            restored.frombytes(bytes(tv.vector))
            if sys.byteorder != "little":
                restored.byteswap()
            self.assertEqual(len(restored), 2)
            self.assertAlmostEqual(restored[0], float(values[0]), places=5)
            self.assertAlmostEqual(restored[1], float(values[1]), places=5)

    def test_is_idempotent(self):
        _write_vectors_gz(self.data_file)
        self._load()
        self._load()
        self.assertEqual(ToneVector.objects.count(), 3)

    def test_clear_removes_existing_rows_before_load(self):
        ToneVector.objects.create(word="old", vector=b"\x00")
        _write_vectors_gz(self.data_file)
        out, _ = self._load(clear=True)
        self.assertIn("Cleared 1 existing rows", out)
        self.assertEqual(ToneVector.objects.count(), 3)
        self.assertFalse(ToneVector.objects.filter(word="old").exists())

    def test_setup_downloads_missing_file_automatically(self):
        missing = Path(self.tmpdir.name) / "missing.gz"
        with patch(
            "tone.management.commands.load_vectors.urlretrieve"
        ) as mock_retrieve:

            def fake_download(url, dest):
                _write_vectors_gz(Path(dest))

            mock_retrieve.side_effect = fake_download
            out, _ = self._load(file=str(missing))

        mock_retrieve.assert_called_once()
        self.assertTrue(missing.is_file())
        self.assertIn("Download complete", out)
        self.assertEqual(ToneVector.objects.count(), 3)

    def test_load_missing_file_raises(self):
        command = Command()
        with self.assertRaisesMessage(
            CommandError, f"Numberbatch file does not exist: {self.data_file}"
        ):
            command._load_vectors(self.data_file, clear=False)

    def test_failed_download_removes_partial_file(self):
        missing = Path(self.tmpdir.name) / "missing.gz"
        partial = missing.with_name(missing.name + ".part")

        def failed_download(url, dest):
            Path(dest).write_bytes(b"incomplete download")
            raise OSError("download failed")

        with patch(
            "tone.management.commands.load_vectors.urlretrieve",
            side_effect=failed_download,
        ):
            with self.assertRaisesMessage(OSError, "download failed"):
                self._load(file=str(missing))

        self.assertFalse(missing.exists())
        self.assertFalse(partial.exists())
        self.assertEqual(ToneVector.objects.count(), 0)

    def test_invalid_header_raises(self):
        with gzip.open(self.data_file, "wt", encoding="utf-8") as fh:
            fh.write("bad header line\n")
        with self.assertRaisesMessage(CommandError, "invalid header"):
            self._load()

    def test_wrong_dimension_raises(self):
        with gzip.open(self.data_file, "wt", encoding="utf-8") as fh:
            fh.write("1 3\n")
            fh.write("word 0.1 0.2\n")  # only 2 values, header says 3
        with self.assertRaisesMessage(CommandError, "Invalid vector on line"):
            self._load()

    def test_header_count_mismatch_warns(self):
        _write_vectors_gz(self.data_file, header_count=999)
        _, err = self._load()
        self.assertIn("999", err)

    def test_skips_loading_when_vectors_already_exist(self):
        _write_vectors_gz(self.data_file)
        self._load()
        original = array("f")
        original.frombytes(bytes(ToneVector.objects.get(word="cat").vector))
        if sys.byteorder != "little":
            original.byteswap()
        # Rewrite with different values for cat.
        updated = [
            ("cat", ["9.0", "-9.0"]),
            ("dog", ["0.3", "0.4"]),
            ("bird", ["-0.5", "0.6"]),
        ]
        _write_vectors_gz(self.data_file, vectors=updated)
        out, _ = self._load()
        self.assertEqual(ToneVector.objects.count(), 3)
        new = array("f")
        new.frombytes(bytes(ToneVector.objects.get(word="cat").vector))
        if sys.byteorder != "little":
            new.byteswap()
        self.assertIn("Vectors already loaded; skipping.", out)
        self.assertAlmostEqual(new[0], original[0], places=5)


class ToneSimilarityTests(TestCase):
    def setUp(self):
        self.challenge = Challenge.objects.create(
            name="Tone test",
            slug="tone-test",
            challenge_date="2026-10-31",
            difficulty=1,
            category="social",
            tone="calm",
            required_action="Listen",
        )
        for word, values in {
            "calm": [2, 0],
            "relaxed": [3, 4],
            "angry": [-1, 0],
            "neutral": [0, 1],
            "very": [0, 2],
            "very_calm": [1, 0],
        }.items():
            ToneVector.objects.create(word=word, vector=_vector_bytes(map(str, values)))

    def score(self, first, second):
        from django.urls import reverse

        Challenge.objects.filter(pk=self.challenge.pk).update(tone=second)
        return self.client.get(
            reverse("tone-similarity", args=[self.challenge.pk]), {"answer": first}
        )

    def test_cosine_uses_magnitudes_and_preserves_negative_values(self):
        for first, second, expected in [
            ("calm", "calm", 1),
            ("calm", "relaxed", 0.6),
            ("calm", "neutral", 0),
            ("calm", "angry", -1),
            ("relaxed", "calm", 0.6),
        ]:
            with self.subTest(first=first, second=second):
                response = self.score(first, second)
                self.assertEqual(response.status_code, 200)
                self.assertAlmostEqual(response.json()["similarity"], expected)
                self.assertEqual(response.json()["correct"], expected >= 0.65)
                self.assertEqual(set(response.json()), {"similarity", "correct"})

    def test_normalizes_case_whitespace_and_punctuation(self):
        self.assertAlmostEqual(self.score(" CALM! ", "calm").json()["similarity"], 1)

    def test_prefers_numberbatch_phrase_vector(self):
        self.assertAlmostEqual(self.score("very calm", "calm").json()["similarity"], 1)

    def test_averages_words_for_missing_phrase(self):
        self.assertAlmostEqual(
            self.score("calm neutral", "calm").json()["similarity"], 2 / (5**0.5)
        )

    def test_unknown_words_are_not_silently_ignored(self):
        for first, second in [
            ("unknown", "calm"),
            ("calm unknown", "calm"),
        ]:
            with self.subTest(first=first, second=second):
                self.assertEqual(self.score(first, second).status_code, 404)

    def test_invalid_input(self):
        for tone in ["!!!", " ", "a" * 201]:
            with self.subTest(tone=tone):
                self.assertEqual(self.score(tone, "calm").status_code, 400)

    def test_unloaded_database_is_unavailable(self):
        ToneVector.objects.all().delete()
        self.assertEqual(self.score("calm", "calm").status_code, 503)

    def test_invalid_vectors_are_unavailable(self):
        for values in [[], [0, 0], [1], [float("nan"), 1], [float("inf"), 1]]:
            ToneVector.objects.filter(word="calm").update(
                vector=_vector_bytes(map(str, values))
            )
            with self.subTest(values=values):
                self.assertEqual(self.score("calm", "neutral").status_code, 503)
        ToneVector.objects.filter(word="calm").update(vector=b"invalid")
        self.assertEqual(self.score("calm", "neutral").status_code, 503)

    def test_only_get_is_allowed(self):
        self.assertEqual(
            self.client.post(f"/api/tone/{self.challenge.pk}/").status_code, 405
        )

    def test_missing_reference_embedding_is_unavailable(self):
        self.assertEqual(self.score("calm", "unknown").status_code, 503)

    def test_missing_or_invalid_answer(self):
        url = f"/api/tone/{self.challenge.pk}/"
        self.assertEqual(self.client.get(url).status_code, 400)

    def test_missing_challenge(self):
        response = self.client.get("/api/tone/999999/", {"answer": "calm"})
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {"detail": "Challenge not found."})

    def test_client_cannot_override_reference_tone(self):
        response = self.client.get(
            f"/api/tone/{self.challenge.pk}/",
            {"answer": "angry", "expected": "angry", "tone": "angry"},
        )
        self.assertEqual(response.json(), {"similarity": -1.0, "correct": False})

    def test_old_two_tone_endpoint_is_removed(self):
        self.assertEqual(self.client.get("/api/tone/calm&calm/").status_code, 404)
