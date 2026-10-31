"""Shared fixtures and package builders for challenge tests."""

import io
import json
import tempfile
import zipfile
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings

from . import package
from .models import Challenge

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

VALID_MP3_PATH = Path(__file__).resolve().parent / "test_data" / "tone.mp3"
VALID_MP3_BYTES = VALID_MP3_PATH.read_bytes()


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


def relative_tree():
    tree = deepcopy(VALID_TREE)

    def rewrite(node):
        key = node["node_key"]
        node["text_file"] = f"transcripts/{key}.txt"
        node["audio_file"] = f"audio/{key}.mp3"
        for child in node["children"]:
            rewrite(child)

    rewrite(tree)
    return tree


def walk_tree(node):
    yield node
    for child in node["children"]:
        yield from walk_tree(child)


def challenge_manifest(slug="greeting", **overrides):
    manifest = {
        "name": "Greeting",
        "slug": slug,
        "challenge_date": "2026-10-15",
        "difficulty": 1,
        "category": "social",
        "tone": "friendly",
        "required_action": "greet warmly",
        "conversation_tree": relative_tree(),
    }
    manifest.update(overrides)
    return manifest


def make_zip(
    manifest=None,
    *,
    folder_name=None,
    extra_entries=None,
    audio_bytes=None,
):
    manifest = manifest or challenge_manifest()
    folder_name = folder_name or manifest["slug"]
    audio_bytes = VALID_MP3_BYTES if audio_bytes is None else audio_bytes
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(
            f"{folder_name}/{folder_name}.json",
            json.dumps(manifest),
        )
        for node in walk_tree(manifest["conversation_tree"]):
            key = node["node_key"]
            archive.writestr(
                f"{folder_name}/transcripts/{key}.txt",
                f"Transcript for {key}\n",
            )
            archive.writestr(
                f"{folder_name}/audio/{key}.mp3",
                audio_bytes,
            )
        for name, content in (extra_entries or {}).items():
            archive.writestr(name, content)
    return SimpleUploadedFile(
        "challenge.zip",
        buffer.getvalue(),
        content_type="application/zip",
    )


def make_zip_from_folder(folder):
    folder = Path(folder)
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(folder.rglob("*")):
            if path.is_file():
                archive.write(
                    path,
                    f"{folder.name}/{path.relative_to(folder).as_posix()}",
                )
    return SimpleUploadedFile(
        "challenge.zip",
        buffer.getvalue(),
        content_type="application/zip",
    )


def write_package(root, manifest, *, audio_bytes=None):
    root = Path(root)
    slug = manifest["slug"]
    folder = root / slug
    audio_bytes = VALID_MP3_BYTES if audio_bytes is None else audio_bytes
    for node in walk_tree(manifest["conversation_tree"]):
        key = node["node_key"]
        transcript = folder / "transcripts" / f"{key}.txt"
        transcript.parent.mkdir(parents=True, exist_ok=True)
        transcript.write_text(f"Transcript for {key}\n", encoding="utf-8")
        audio = folder / "audio" / f"{key}.mp3"
        audio.parent.mkdir(parents=True, exist_ok=True)
        audio.write_bytes(audio_bytes)
    folder.mkdir(parents=True, exist_ok=True)
    (folder / f"{slug}.json").write_text(json.dumps(manifest), encoding="utf-8")
    return folder


class MediaTestCase(TestCase):
    def setUp(self):
        super().setUp()
        media = tempfile.TemporaryDirectory()
        self.addCleanup(media.cleanup)
        self.media = Path(media.name)
        settings_override = override_settings(MEDIA_ROOT=media.name)
        settings_override.enable()
        self.addCleanup(settings_override.disable)

        source = tempfile.TemporaryDirectory()
        self.addCleanup(source.cleanup)
        self.source = Path(source.name)
        source_override = patch("challenges.package.CHALLENGES_DIR", self.source)
        source_override.start()
        self.addCleanup(source_override.stop)
