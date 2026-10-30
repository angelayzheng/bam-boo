"""Validate and install local and uploaded challenge packages."""

import json
import logging
import shutil
import stat
import tempfile
import threading
import zipfile
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import validate_slug
from django.db import transaction

from .models import Challenge, validate_conversation_tree

try:
    import fcntl
except ImportError:
    fcntl = None

logger = logging.getLogger(__name__)

_IMPORT_LOCK = threading.Lock()

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

ALLOWED_ARCHIVE_SUFFIXES = {".json", ".mp3", ".txt"}
IGNORED_ARCHIVE_FILENAMES = {".DS_Store", "Thumbs.db", "desktop.ini"}
WINDOWS_RESERVED_NAMES = {
    "CON",
    "PRN",
    "AUX",
    "NUL",
    "COM1",
    "COM2",
    "COM3",
    "COM4",
    "COM5",
    "COM6",
    "COM7",
    "COM8",
    "COM9",
    "LPT1",
    "LPT2",
    "LPT3",
    "LPT4",
    "LPT5",
    "LPT6",
    "LPT7",
    "LPT8",
    "LPT9",
}

DEFAULT_MAX_ARCHIVE_BYTES = 200 * 1024 * 1024
DEFAULT_MAX_UNCOMPRESSED_BYTES = 400 * 1024 * 1024
DEFAULT_MAX_FILES = 200


class ChallengePackageError(Exception):
    """A challenge package cannot be validated or installed."""


@dataclass(frozen=True)
class PreparedChallenge:
    challenge: Challenge
    folder: Path
    files: frozenset[str]
    replaced: bool
    turn_count: int


@dataclass(frozen=True)
class ImportResult:
    challenge: Challenge
    replaced: bool
    turn_count: int


def prepare_challenge_package(folder, *, replace=False, skip_existing=False):
    """Validate a complete package before changing any files or records."""
    folder = Path(folder)
    if not folder.is_dir():
        raise ChallengePackageError(f"Challenge package directory not found: {folder}")

    try:
        manifest_path = folder / f"{folder.name}.json"
        if manifest_path.is_symlink():
            raise ChallengePackageError("The manifest must not be a symbolic link.")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        values = {key: manifest[key] for key in METADATA_FIELDS}
        if values["slug"] != folder.name:
            raise ChallengePackageError("slug must match its folder name.")

        existing = Challenge.objects.filter(slug=values["slug"]).first()
        if existing and not replace:
            if skip_existing:
                return None
            raise ChallengePackageError(
                f"Challenge {values['slug']!r} already exists; "
                "select Replace to update it."
            )

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
                resolved[field] = f"challenges/{values['slug']}/{relative}"
            resolved["children"] = [
                resolve(child) for child in node.get("children", [])
            ]
            return resolved

        challenge = existing or Challenge()
        for key, value in values.items():
            setattr(challenge, key, value)
        challenge.conversation_tree = resolve(tree)
        challenge.full_clean()
        return PreparedChallenge(
            challenge=challenge,
            folder=folder,
            files=frozenset(files),
            replaced=existing is not None,
            turn_count=len(files) // 2,
        )
    except ChallengePackageError:
        raise
    except (OSError, ValueError, KeyError, TypeError, ValidationError) as exc:
        raise ChallengePackageError(
            f"Invalid challenge package {folder.name}: {exc}"
        ) from exc


def _remove_path(path):
    if path.is_dir() and not path.is_symlink():
        shutil.rmtree(path)
    elif path.exists() or path.is_symlink():
        path.unlink()


@contextmanager
def _import_lock(challenges_root):
    if fcntl is None:
        with _IMPORT_LOCK:
            yield
        return
    lock_path = Path(challenges_root).parent / ".challenge-import.lock"
    with lock_path.open("a+") as lock_file:
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)


def install_challenge(prepared):
    """Stage a complete challenge and restore the previous directory on failure."""
    challenge = prepared.challenge
    challenges_root = Path(settings.MEDIA_ROOT) / "challenges"
    challenges_root.mkdir(parents=True, exist_ok=True)
    destination = challenges_root / challenge.slug
    with tempfile.TemporaryDirectory(
        prefix=".import-", dir=challenges_root
    ) as temporary:
        temporary = Path(temporary)
        staged = temporary / "new"
        staged.mkdir()
        shutil.copyfile(
            prepared.folder / f"{challenge.slug}.json",
            staged / f"{challenge.slug}.json",
        )
        for relative in prepared.files:
            target = staged / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(prepared.folder / relative, target)
        backup = temporary / "previous"
        with _import_lock(challenges_root):
            had_previous = destination.exists()
            if had_previous:
                destination.rename(backup)
            try:
                with transaction.atomic():
                    challenge.save()
                    staged.rename(destination)
            except Exception:
                _remove_path(destination)
                if had_previous:
                    backup.rename(destination)
                raise
        logger.info(
            "Installed challenge package %s with %s turns.",
            challenge.slug,
            prepared.turn_count,
        )


def import_challenge_package(folder, *, replace=False, skip_existing=False):
    """Validate and install one package folder."""
    prepared = prepare_challenge_package(
        folder,
        replace=replace,
        skip_existing=skip_existing,
    )
    if prepared is None:
        return None
    try:
        install_challenge(prepared)
    except OSError as exc:
        logger.exception(
            "Could not install challenge package %s.", prepared.challenge.slug
        )
        raise ChallengePackageError(f"Could not save challenge files: {exc}") from exc
    return ImportResult(
        challenge=prepared.challenge,
        replaced=prepared.replaced,
        turn_count=prepared.turn_count,
    )


def _setting(name, default):
    return getattr(settings, name, default)


def _uploaded_file_size(uploaded_file):
    size = getattr(uploaded_file, "size", None)
    if size is not None:
        return size
    uploaded_file.seek(0, 2)
    size = uploaded_file.tell()
    uploaded_file.seek(0)
    return size


def _is_ignored_archive_member(name):
    parts = tuple(part for part in name.split("/") if part)
    if not parts:
        return True
    if parts[0] == "__MACOSX":
        return True
    if parts[-1] in IGNORED_ARCHIVE_FILENAMES:
        return True
    return parts[-1].startswith("._")


def _validate_archive_path(name):
    if not name or "\x00" in name:
        raise ChallengePackageError("The ZIP contains an invalid empty path.")
    if "\\" in name:
        raise ChallengePackageError(
            f"The ZIP contains a path with a backslash: {name!r}."
        )
    if name.startswith("/"):
        raise ChallengePackageError(f"The ZIP contains an absolute path: {name!r}.")
    if any(ord(character) < 32 for character in name):
        raise ChallengePackageError(
            f"The ZIP contains a path with control characters: {name!r}."
        )

    pure = PurePosixPath(name)
    if pure.is_absolute():
        raise ChallengePackageError(f"The ZIP contains an absolute path: {name!r}.")
    if any(part in ("", ".", "..") for part in pure.parts):
        raise ChallengePackageError(f"The ZIP contains a path traversal: {name!r}.")
    if ":" in name:
        raise ChallengePackageError(f"The ZIP contains a path with a colon: {name!r}.")
    for part in pure.parts:
        if part.endswith((" ", ".")):
            raise ChallengePackageError(
                f"The ZIP contains a path with a trailing space or dot: {name!r}."
            )
        stem = part.split(".", 1)[0].upper()
        if stem in WINDOWS_RESERVED_NAMES:
            raise ChallengePackageError(
                f"The ZIP contains a reserved filename: {name!r}."
            )


def _validate_archive_members(archive, members):
    max_files = _setting("CHALLENGE_IMPORT_MAX_FILES", DEFAULT_MAX_FILES)
    max_uncompressed = _setting(
        "CHALLENGE_IMPORT_MAX_UNCOMPRESSED_BYTES",
        DEFAULT_MAX_UNCOMPRESSED_BYTES,
    )
    file_count = 0
    uncompressed_size = 0
    seen_names = set()

    for info in members:
        name = info.filename
        _validate_archive_path(name)
        if info.flag_bits & 0x1:
            raise ChallengePackageError(
                f"The ZIP contains an encrypted file: {name!r}."
            )
        mode = info.external_attr >> 16
        if stat.S_ISLNK(mode):
            raise ChallengePackageError(f"The ZIP contains a symbolic link: {name!r}.")
        if info.is_dir():
            continue
        suffix = PurePosixPath(name).suffix.lower()
        if suffix not in ALLOWED_ARCHIVE_SUFFIXES:
            raise ChallengePackageError(
                f"The ZIP contains an unsupported file type: {name!r}."
            )
        casefolded = name.casefold()
        if casefolded in seen_names:
            raise ChallengePackageError(f"The ZIP contains a duplicate file: {name!r}.")
        seen_names.add(casefolded)
        file_count += 1
        if file_count > max_files:
            raise ChallengePackageError(
                f"The ZIP contains more than {max_files} files."
            )
        uncompressed_size += info.file_size
        if uncompressed_size > max_uncompressed:
            raise ChallengePackageError(
                "The ZIP expands beyond the allowed uncompressed size."
            )


def _extract_members(archive, members, destination):
    max_uncompressed = _setting(
        "CHALLENGE_IMPORT_MAX_UNCOMPRESSED_BYTES",
        DEFAULT_MAX_UNCOMPRESSED_BYTES,
    )
    destination_root = destination.resolve()
    written_total = 0

    for info in members:
        if info.is_dir():
            continue
        relative = PurePosixPath(info.filename)
        target = destination.joinpath(*relative.parts)
        if not target.resolve().is_relative_to(destination_root):
            raise ChallengePackageError(
                f"The ZIP contains an unsafe path: {info.filename!r}."
            )
        target.parent.mkdir(parents=True, exist_ok=True)
        try:
            with archive.open(info) as source, target.open("wb") as output:
                while True:
                    chunk = source.read(1024 * 1024)
                    if not chunk:
                        break
                    written_total += len(chunk)
                    if written_total > max_uncompressed:
                        raise ChallengePackageError(
                            "The ZIP expands beyond the allowed uncompressed size."
                        )
                    output.write(chunk)
        except ChallengePackageError:
            raise
        except (OSError, RuntimeError, NotImplementedError) as exc:
            raise ChallengePackageError(
                f"Could not extract {info.filename!r}: {exc}"
            ) from exc


def extract_challenge_archive(uploaded_file, destination):
    """Safely extract a ZIP and return its single package folder."""
    destination = Path(destination)
    try:
        uploaded_file.seek(0)
        if not zipfile.is_zipfile(uploaded_file):
            raise ChallengePackageError("Upload a valid .zip archive.")
        uploaded_file.seek(0)
        with zipfile.ZipFile(uploaded_file) as archive:
            members = [
                info
                for info in archive.infolist()
                if not _is_ignored_archive_member(info.filename)
            ]
            if not members:
                raise ChallengePackageError("The ZIP is empty.")
            _validate_archive_members(archive, members)
            _extract_members(archive, members, destination)
    except ChallengePackageError:
        raise
    except (zipfile.BadZipFile, zipfile.LargeZipFile) as exc:
        raise ChallengePackageError("Upload a valid .zip archive.") from exc
    except (OSError, RuntimeError, NotImplementedError) as exc:
        raise ChallengePackageError(f"Could not read the ZIP archive: {exc}") from exc

    entries = [
        path
        for path in destination.iterdir()
        if not _is_ignored_archive_member(path.name)
    ]
    if len(entries) != 1 or not entries[0].is_dir():
        raise ChallengePackageError(
            "The ZIP must contain exactly one top-level challenge folder named after the slug."
        )
    return entries[0]


def import_challenge_archive(uploaded_file, *, replace=False, skip_existing=False):
    """Validate and install a ZIP package without touching the source tree."""
    max_archive = _setting(
        "CHALLENGE_IMPORT_MAX_ARCHIVE_BYTES",
        DEFAULT_MAX_ARCHIVE_BYTES,
    )
    try:
        if _uploaded_file_size(uploaded_file) > max_archive:
            raise ChallengePackageError(
                f"The ZIP must be {max_archive // (1024 * 1024)} MB or smaller."
            )
        with tempfile.TemporaryDirectory(prefix="challenge-import-") as temporary:
            folder = extract_challenge_archive(uploaded_file, temporary)
            return import_challenge_package(
                folder,
                replace=replace,
                skip_existing=skip_existing,
            )
    except ChallengePackageError:
        raise
    except OSError as exc:
        raise ChallengePackageError(
            f"Could not read the challenge package: {exc}"
        ) from exc
