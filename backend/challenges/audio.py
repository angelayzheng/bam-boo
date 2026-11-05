"""FFprobe validation for challenge audio files."""

import json
import math
import subprocess
from dataclasses import dataclass
from pathlib import Path

FFPROBE_TIMEOUT_SECONDS = 30


class AudioValidationError(Exception):
    """An audio file cannot be validated as playable MP3 audio."""


@dataclass(frozen=True)
class AudioInfo:
    codec_name: str
    duration: float


def probe_audio(path):
    """Return validated audio metadata or raise AudioValidationError."""
    command = [
        "ffprobe",
        "-v",
        "error",
        "-select_streams",
        "a:0",
        "-show_entries",
        "stream=codec_name,duration:format=duration",
        "-of",
        "json",
        str(path),
    ]
    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            check=False,
            text=True,
            timeout=FFPROBE_TIMEOUT_SECONDS,
        )
    except FileNotFoundError as exc:
        raise AudioValidationError(
            "ffprobe is required to validate challenge audio. Install FFmpeg."
        ) from exc
    except subprocess.TimeoutExpired as exc:
        raise AudioValidationError(
            f"ffprobe timed out after {FFPROBE_TIMEOUT_SECONDS} seconds."
        ) from exc

    if completed.returncode:
        detail = completed.stderr.strip() or "ffprobe could not read the file."
        raise AudioValidationError(detail)

    try:
        payload = json.loads(completed.stdout)
    except (TypeError, ValueError) as exc:
        raise AudioValidationError("ffprobe returned invalid JSON.") from exc
    if not isinstance(payload, dict):
        raise AudioValidationError("ffprobe returned invalid JSON.")

    streams = payload.get("streams")
    if not isinstance(streams, list) or not streams:
        raise AudioValidationError("The file contains no audio stream.")
    stream = streams[0]
    if not isinstance(stream, dict):
        raise AudioValidationError("ffprobe returned invalid stream data.")
    codec_name = stream.get("codec_name")
    if codec_name != "mp3":
        raise AudioValidationError(
            f"Expected MP3 audio, found {codec_name or 'an unknown codec'}."
        )

    format_payload = payload.get("format")
    if not isinstance(format_payload, dict):
        format_payload = {}
    for raw_duration in (stream.get("duration"), format_payload.get("duration")):
        try:
            duration = float(raw_duration)
        except TypeError, ValueError:
            continue
        if math.isfinite(duration) and duration > 0:
            return AudioInfo(codec_name=codec_name, duration=duration)

    raise AudioValidationError("The audio duration is missing or invalid.")


def validate_audio_file(path):
    return probe_audio(Path(path))
