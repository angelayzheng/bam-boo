"""Load and structurally validate challenge packages."""

import json
from dataclasses import dataclass
from pathlib import Path

from django.core.exceptions import ValidationError
from django.core.validators import validate_slug

from .models import validate_conversation_tree

CHALLENGES_DIR = Path(__file__).resolve().parent / "source_data" / "challenges"

METADATA_FIELDS = (
    "name",
    "slug",
    "challenge_date",
    "difficulty",
    "category",
    "tone",
    "required_action",
)


class ChallengePackageError(Exception):
    """A challenge package cannot be loaded or validated."""


@dataclass(frozen=True)
class ChallengePackage:
    folder: Path
    metadata: dict
    conversation_tree: dict
    files: frozenset[str]
    turn_count: int

    @property
    def slug(self):
        return self.metadata["slug"]


def iter_conversation_nodes(tree):
    yield tree
    for child in tree.get("children", []):
        yield from iter_conversation_nodes(child)


def load_challenge_package(folder):
    """Load a package without touching the database or probing audio."""
    folder = Path(folder)
    if not folder.is_dir():
        raise ChallengePackageError(f"Challenge package directory not found: {folder}")

    try:
        manifest_path = folder / f"{folder.name}.json"
        if manifest_path.is_symlink():
            raise ChallengePackageError("The manifest must not be a symbolic link.")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        metadata = {key: manifest[key] for key in METADATA_FIELDS}
        if metadata["slug"] != folder.name:
            raise ChallengePackageError("slug must match its folder name.")

        tree = manifest["conversation_tree"]
        if not tree:
            raise ChallengePackageError(
                "conversation_tree must contain a customer opening."
            )
        validate_conversation_tree(tree)
        files = set()

        def resolve(node):
            if not node.get("node_key"):
                raise ChallengePackageError("Every turn must have a unique node_key.")
            validate_slug(node["node_key"])
            resolved = {**node}
            for field, directory, extension in (
                ("text_file", "transcripts", ".txt"),
                ("audio_file", "audio", ".mp3"),
            ):
                relative = f"{directory}/{node['node_key']}{extension}"
                if node[field] != relative:
                    raise ChallengePackageError(f"{field} must be {relative!r}.")
                source = folder / relative
                if (
                    source.is_symlink()
                    or not source.is_file()
                    or not source.stat().st_size
                ):
                    raise ChallengePackageError(f"Missing or empty file: {relative}")
                if (
                    field == "text_file"
                    and not source.read_text(encoding="utf-8").strip()
                ):
                    raise ChallengePackageError(f"Empty transcript: {relative}")
                files.add(relative)
                resolved[field] = f"challenges/{metadata['slug']}/{relative}"
            resolved["children"] = [
                resolve(child) for child in node.get("children", [])
            ]
            return resolved

        return ChallengePackage(
            folder=folder,
            metadata=metadata,
            conversation_tree=resolve(tree),
            files=frozenset(files),
            turn_count=len(files) // 2,
        )
    except ChallengePackageError:
        raise
    except (OSError, ValueError, KeyError, TypeError, ValidationError) as exc:
        raise ChallengePackageError(
            f"Invalid challenge package {folder.name}: {exc}"
        ) from exc
