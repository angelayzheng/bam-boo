#!/usr/bin/env python3
"""Normalize challenge MP3 files in place using FFmpeg's two-pass loudnorm filter."""

import argparse
import json
import math
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_AUDIO_ROOT = (
    REPOSITORY_ROOT / "backend" / "challenges" / "source_data" / "challenges"
)
TARGET_LOUDNESS = -23.0
TARGET_TRUE_PEAK = -1.5
LOUDNESS_TOLERANCE = 1.0
LOUDNORM_REPORT = re.compile(r'\{\s*"input_i".*?\n\}', re.DOTALL)


def measure_audio(path, ffmpeg):
    result = subprocess.run(
        [
            ffmpeg,
            "-hide_banner",
            "-nostats",
            "-i",
            str(path),
            "-af",
            (
                f"loudnorm=I={TARGET_LOUDNESS}:LRA=7:"
                f"TP={TARGET_TRUE_PEAK}:print_format=json"
            ),
            "-f",
            "null",
            "-",
        ],
        capture_output=True,
        check=False,
        text=True,
    )
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or "FFmpeg could not read the file.")

    match = LOUDNORM_REPORT.search(result.stderr)
    if match is None:
        raise RuntimeError("FFmpeg did not return loudness measurements.")

    try:
        report = json.loads(match.group())
        measurement = {
            "input_i": float(report["input_i"]),
            "input_tp": float(report["input_tp"]),
            "input_lra": float(report["input_lra"]),
            "input_thresh": float(report["input_thresh"]),
            "target_offset": float(report["target_offset"]),
        }
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
        raise RuntimeError(f"Invalid loudness measurements: {error}") from error

    if not all(math.isfinite(value) for value in measurement.values()):
        raise RuntimeError("The file has no measurable audio loudness.")
    return measurement


def normalize_audio(path, ffmpeg):
    current = measure_audio(path, ffmpeg)
    if (
        abs(current["input_i"] - TARGET_LOUDNESS) <= LOUDNESS_TOLERANCE
        and current["input_tp"] <= TARGET_TRUE_PEAK
    ):
        return False

    filter_parameters = (
        f"measured_I={current['input_i']}",
        f"measured_TP={current['input_tp']}",
        f"measured_LRA={current['input_lra']}",
        f"measured_thresh={current['input_thresh']}",
        f"offset={current['target_offset']}",
    )
    filter_spec = (
        f"loudnorm=I={TARGET_LOUDNESS}:LRA=7:TP={TARGET_TRUE_PEAK}:"
        + ":".join(filter_parameters)
        + ":linear=true"
    )

    with tempfile.TemporaryDirectory(
        prefix=".normalize-", dir=path.parent
    ) as temporary_directory:
        normalized_path = Path(temporary_directory) / path.name
        result = subprocess.run(
            [
                ffmpeg,
                "-hide_banner",
                "-nostats",
                "-y",
                "-i",
                str(path),
                "-map_metadata",
                "0",
                "-af",
                filter_spec,
                "-c:a",
                "libmp3lame",
                "-b:a",
                "128k",
                str(normalized_path),
            ],
            capture_output=True,
            check=False,
            text=True,
        )
        if result.returncode:
            raise RuntimeError(
                result.stderr.strip() or "FFmpeg could not normalize the file."
            )

        verified = measure_audio(normalized_path, ffmpeg)
        if (
            abs(verified["input_i"] - TARGET_LOUDNESS) > 1.0
            or verified["input_tp"] > TARGET_TRUE_PEAK
        ):
            raise RuntimeError(
                "Normalized output did not meet the target "
                f"({verified['input_i']:.2f} LUFS, "
                f"{verified['input_tp']:.2f} dBTP); original left unchanged."
            )

        shutil.copystat(path, normalized_path)
        normalized_path.replace(path)
    return True


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Normalize MP3 recordings in the challenge source tree to "
            "-23 LUFS and a maximum true peak of -1.5 dBTP."
        )
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=DEFAULT_AUDIO_ROOT,
        help="directory to scan recursively (default: challenge source packages)",
    )
    arguments = parser.parse_args()
    root = arguments.root.expanduser().resolve()
    if not root.is_dir():
        parser.error(f"audio directory does not exist: {root}")

    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        print(
            "Error: FFmpeg is required. Install it and ensure ffmpeg is on PATH.",
            file=sys.stderr,
        )
        return 1

    files = sorted(
        path
        for path in root.rglob("*")
        if path.is_file() and path.suffix.lower() == ".mp3"
    )
    if not files:
        print(f"No MP3 files found under {root}.", file=sys.stderr)
        return 1

    failures = 0
    for path in files:
        try:
            changed = normalize_audio(path, ffmpeg)
        except (OSError, RuntimeError) as error:
            print(f"ERROR {path}: {error}", file=sys.stderr)
            failures += 1
            continue
        state = "normalized" if changed else "already normalized"
        print(f"{state}: {path}")

    if failures:
        print(f"Normalization failed for {failures} of {len(files)} file(s).")
        return 1
    print(f"Checked {len(files)} MP3 file(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
