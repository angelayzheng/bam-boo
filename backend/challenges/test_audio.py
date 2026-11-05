import json
import subprocess
from unittest.mock import patch

from django.test import SimpleTestCase

from .audio import AudioValidationError, probe_audio
from .test_support import VALID_MP3_PATH


class AudioProbeTests(SimpleTestCase):
    def test_reads_real_mp3_metadata(self):
        info = probe_audio(VALID_MP3_PATH)
        self.assertEqual(info.codec_name, "mp3")
        self.assertGreater(info.duration, 0)

    def test_reports_missing_ffprobe(self):
        with patch(
            "challenges.audio.subprocess.run",
            side_effect=FileNotFoundError,
        ):
            with self.assertRaisesMessage(AudioValidationError, "ffprobe is required"):
                probe_audio(VALID_MP3_PATH)

    def test_reports_ffprobe_failure(self):
        completed = subprocess.CompletedProcess(
            args=[],
            returncode=1,
            stdout="",
            stderr="invalid data",
        )
        with patch("challenges.audio.subprocess.run", return_value=completed):
            with self.assertRaisesMessage(AudioValidationError, "invalid data"):
                probe_audio(VALID_MP3_PATH)

    def test_rejects_invalid_json(self):
        completed = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout="not json",
            stderr="",
        )
        with patch("challenges.audio.subprocess.run", return_value=completed):
            with self.assertRaisesMessage(AudioValidationError, "invalid JSON"):
                probe_audio(VALID_MP3_PATH)

    def test_rejects_missing_audio_stream(self):
        completed = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout=json.dumps({"streams": []}),
            stderr="",
        )
        with patch("challenges.audio.subprocess.run", return_value=completed):
            with self.assertRaisesMessage(AudioValidationError, "no audio stream"):
                probe_audio(VALID_MP3_PATH)

    def test_rejects_non_mp3_audio(self):
        completed = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout=json.dumps(
                {
                    "streams": [
                        {"codec_name": "aac", "duration": "1.0"},
                    ]
                }
            ),
            stderr="",
        )
        with patch("challenges.audio.subprocess.run", return_value=completed):
            with self.assertRaisesMessage(AudioValidationError, "Expected MP3"):
                probe_audio(VALID_MP3_PATH)

    def test_rejects_invalid_duration(self):
        completed = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout=json.dumps(
                {
                    "streams": [
                        {"codec_name": "mp3", "duration": "0"},
                    ],
                    "format": {"duration": "N/A"},
                }
            ),
            stderr="",
        )
        with patch("challenges.audio.subprocess.run", return_value=completed):
            with self.assertRaisesMessage(AudioValidationError, "duration is missing"):
                probe_audio(VALID_MP3_PATH)
