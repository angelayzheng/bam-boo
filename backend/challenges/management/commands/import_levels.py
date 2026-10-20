"""Import local level packages without storing audio or transcripts in SQLite."""

import json
import shutil
import tempfile
from pathlib import Path

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import validate_slug
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from challenges.models import Challenge, validate_conversation_tree

LEVELS_DIR = Path(__file__).resolve().parents[2] / "source_data" / "levels"
METADATA_FIELDS = (
    "level_id",
    "name",
    "slug",
    "challenge_date",
    "difficulty",
    "category",
    "tone",
    "required_action",
)


def _prepare_level(folder, replace):
    """Validate the complete package before changing any files or records."""
    try:
        manifest = json.loads((folder / "level.json").read_text(encoding="utf-8"))
        values = {key: manifest[key] for key in METADATA_FIELDS}
        if values["level_id"] != folder.name:
            raise ValueError("level_id must match its folder name.")
        existing = Challenge.objects.filter(level_id=values["level_id"]).first()
        # Recognize legacy demo records by slug so importing preserves their PK.
        if existing is None:
            existing = Challenge.objects.filter(slug=values["slug"]).first()
        if existing and existing.level_id != values["level_id"]:
            raise ValueError("This slug already belongs to a different level_id.")
        if existing and not replace:
            return None

        tree = manifest["conversation_tree"]
        if not tree:
            raise ValueError("conversation_tree must contain a customer opening.")
        validate_conversation_tree(tree)
        files = set()

        def resolve(node):
            if not node.get("node_key"):
                raise ValueError("Every turn must have a unique node_key.")
            validate_slug(node["node_key"])
            speaker = "customer" if node["type"] == "question" else "agent"
            resolved = {**node}
            for field, directory, extension in (
                ("text_file", "transcripts", ".txt"),
                ("audio_file", "audio", ".mp3"),
            ):
                relative = f"{directory}/{speaker}/{node['node_key']}{extension}"
                if node[field] != relative:
                    raise ValueError(f"{field} must be {relative!r}.")
                source = folder / relative
                if not source.is_file() or not source.stat().st_size:
                    raise ValueError(f"Missing or empty file: {relative}")
                if (
                    field == "text_file"
                    and not source.read_text(encoding="utf-8").strip()
                ):
                    raise ValueError(f"Empty transcript: {relative}")
                files.add(relative)
                resolved[field] = f"levels/{values['level_id']}/{relative}"
            resolved["children"] = [
                resolve(child) for child in node.get("children", [])
            ]
            return resolved

        challenge = existing or Challenge()
        for key, value in values.items():
            setattr(challenge, key, value)
        challenge.conversation_tree = resolve(tree)
        challenge.full_clean()
        return challenge, folder, files
    except (OSError, ValueError, KeyError, TypeError, ValidationError) as exc:
        raise CommandError(f"Invalid level package {folder.name}: {exc}") from exc


def _install_level(challenge, folder, files):
    """Stage a complete level; restore the previous directory if saving fails."""
    levels_root = Path(settings.MEDIA_ROOT) / "levels"
    levels_root.mkdir(parents=True, exist_ok=True)
    destination = levels_root / challenge.level_id
    with tempfile.TemporaryDirectory(prefix=".import-", dir=levels_root) as temporary:
        temporary = Path(temporary)
        staged = temporary / "new"
        staged.mkdir()
        shutil.copyfile(folder / "level.json", staged / "level.json")
        for relative in files:
            target = staged / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(folder / relative, target)
        backup = temporary / "previous"
        had_previous = destination.exists()
        if had_previous:
            destination.rename(backup)
        try:
            with transaction.atomic():
                challenge.save()
                staged.rename(destination)
        except Exception:
            if destination.exists():
                shutil.rmtree(destination)
            if had_previous:
                backup.rename(destination)
            raise


class Command(BaseCommand):
    help = "Import all local level packages, or only the specified level IDs."

    def add_arguments(self, parser):
        parser.add_argument("level_ids", nargs="*")
        parser.add_argument(
            "--replace",
            action="store_true",
            help="Replace existing levels and their media, preserving database IDs.",
        )

    def handle(self, *args, **options):
        if not LEVELS_DIR.is_dir():
            raise CommandError(f"Level source directory not found: {LEVELS_DIR}")
        available = {path.name: path for path in LEVELS_DIR.iterdir() if path.is_dir()}
        requested = options["level_ids"] or sorted(available)
        missing = set(requested) - available.keys()
        if missing:
            raise CommandError(f"Unknown level IDs: {', '.join(sorted(missing))}")
        if not requested:
            raise CommandError(f"No level packages found in {LEVELS_DIR}.")
        # Validate every selected package before installing any of them.
        prepared = [
            _prepare_level(available[level_id], options["replace"])
            for level_id in dict.fromkeys(requested)
        ]
        for field in ("name", "slug"):
            seen = set()
            for package in prepared:
                if package is not None:
                    value = getattr(package[0], field)
                    if value in seen:
                        raise CommandError(
                            f"Selected levels have a duplicate {field}: {value}"
                        )
                    seen.add(value)
        for package in prepared:
            if package is None:
                self.stdout.write("Level already exists; use --replace to update it.")
                continue
            challenge, folder, files = package
            _install_level(challenge, folder, files)
            self.stdout.write(
                self.style.SUCCESS(
                    f"Imported {challenge.level_id}: {challenge.name} ({len(files) // 2} turns)."
                )
            )
