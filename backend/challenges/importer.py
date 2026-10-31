"""Import validated challenge packages into source and media storage."""

import logging
import shutil
import stat
import tempfile
import threading
import zipfile
from contextlib import ExitStack, contextmanager
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from . import package
from .audio import AudioValidationError, validate_audio_file
from .models import Challenge

try:
    import fcntl
except ImportError:
    fcntl = None

logger = logging.getLogger(__name__)

_IMPORT_LOCK = threading.Lock()

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


@dataclass(frozen=True)
class PreparedChallenge:
    challenge: Challenge
    source_package: package.ChallengePackage
    replaced: bool

    @property
    def turn_count(self):
        return self.source_package.turn_count


@dataclass(frozen=True)
class ImportResult:
    challenge: Challenge
    replaced: bool
    turn_count: int


def _validate_package_audio(source_package):
    for relative in sorted(source_package.files):
        if not relative.startswith("audio/"):
            continue
        try:
            validate_audio_file(source_package.folder / relative)
        except AudioValidationError as exc:
            raise AudioValidationError(f"{relative}: {exc}") from exc


def prepare_challenge_package(folder, *, replace=False, skip_existing=False):
    """Validate a complete package before changing any files or records."""
    folder = Path(folder)
    try:
        source_package = package.load_challenge_package(folder)
        existing = Challenge.objects.filter(slug=source_package.slug).first()
        if existing and not replace:
            if skip_existing:
                return None
            raise package.ChallengePackageError(
                f"Challenge {source_package.slug!r} already exists; "
                "select Replace to update it."
            )

        _validate_package_audio(source_package)
        challenge = existing or Challenge()
        for key, value in source_package.metadata.items():
            setattr(challenge, key, value)
        challenge.conversation_tree = source_package.conversation_tree
        challenge.full_clean()
        return PreparedChallenge(
            challenge=challenge,
            source_package=source_package,
            replaced=existing is not None,
        )
    except package.ChallengePackageError:
        raise
    except (
        AudioValidationError,
        OSError,
        ValueError,
        KeyError,
        TypeError,
        ValidationError,
    ) as exc:
        raise package.ChallengePackageError(
            f"Invalid challenge package {folder.name}: {exc}"
        ) from exc


def _remove_path(path):
    if path.is_dir() and not path.is_symlink():
        shutil.rmtree(path)
    elif path.exists() or path.is_symlink():
        path.unlink()


@contextmanager
def _import_lock(media_root):
    if fcntl is None:
        with _IMPORT_LOCK:
            yield
        return
    lock_path = Path(media_root).parent / ".challenge-import.lock"
    with lock_path.open("a+") as lock_file:
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)


def _stage_package(source_package, parent, slug):
    temporary = tempfile.TemporaryDirectory(prefix=".import-", dir=parent)
    staged = Path(temporary.name) / "new"
    staged.mkdir()
    try:
        shutil.copyfile(
            source_package.folder / f"{slug}.json",
            staged / f"{slug}.json",
        )
        for relative in source_package.files:
            target = staged / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source_package.folder / relative, target)
    except Exception:
        temporary.cleanup()
        raise
    return temporary, staged


def _published_source_destination(source_package):
    return Path(package.CHALLENGES_DIR) / source_package.slug


def _needs_source_install(source_package):
    destination = _published_source_destination(source_package)
    return source_package.folder.resolve() != destination.resolve()


def _install_challenge(prepared):
    """Stage and atomically install the media and optional source package."""
    challenge = prepared.challenge
    source_package = prepared.source_package
    media_root = Path(settings.MEDIA_ROOT) / "challenges"
    media_root.mkdir(parents=True, exist_ok=True)
    media_destination = media_root / challenge.slug

    install_source = _needs_source_install(source_package)
    source_root = Path(package.CHALLENGES_DIR)
    if install_source:
        source_root.mkdir(parents=True, exist_ok=True)
    source_destination = source_root / challenge.slug

    with ExitStack() as stack:
        media_temporary, media_staged = _stage_package(
            source_package, media_root, challenge.slug
        )
        stack.callback(media_temporary.cleanup)
        source_temporary = None
        source_staged = None
        if install_source:
            source_temporary, source_staged = _stage_package(
                source_package, source_root, challenge.slug
            )
            stack.callback(source_temporary.cleanup)

        with _import_lock(media_root):
            media_backup = Path(media_temporary.name) / "previous"
            source_backup = (
                Path(source_temporary.name) / "previous"
                if source_temporary is not None
                else None
            )
            media_previous = media_destination.exists()
            source_previous = install_source and source_destination.exists()
            media_installed = False
            source_installed = False
            try:
                if media_previous:
                    media_destination.rename(media_backup)
                if source_previous:
                    source_destination.rename(source_backup)
                with transaction.atomic():
                    challenge.save()
                    media_staged.rename(media_destination)
                    media_installed = True
                    if source_staged is not None:
                        source_staged.rename(source_destination)
                        source_installed = True
            except Exception:
                if source_installed:
                    _remove_path(source_destination)
                if media_installed:
                    _remove_path(media_destination)
                if source_previous and source_backup.exists():
                    source_backup.rename(source_destination)
                if media_previous and media_backup.exists():
                    media_backup.rename(media_destination)
                raise

    logger.info(
        "Installed challenge package %s with %s turns.",
        challenge.slug,
        prepared.turn_count,
    )


def install_challenge(prepared):
    """Install a prepared challenge, converting expected failures to package errors."""
    try:
        _install_challenge(prepared)
    except (IntegrityError, OSError, ValidationError) as exc:
        logger.exception(
            "Could not install challenge package %s.", prepared.challenge.slug
        )
        raise package.ChallengePackageError(
            f"Could not save challenge files: {exc}"
        ) from exc


def import_challenge_package(folder, *, replace=False, skip_existing=False):
    """Validate and install one package folder."""
    prepared = prepare_challenge_package(
        folder,
        replace=replace,
        skip_existing=skip_existing,
    )
    if prepared is None:
        return None
    install_challenge(prepared)
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
        raise package.ChallengePackageError("The ZIP contains an invalid empty path.")
    if "\\" in name:
        raise package.ChallengePackageError(
            f"The ZIP contains a path with a backslash: {name!r}."
        )
    if name.startswith("/"):
        raise package.ChallengePackageError(
            f"The ZIP contains an absolute path: {name!r}."
        )
    if any(ord(character) < 32 for character in name):
        raise package.ChallengePackageError(
            f"The ZIP contains a path with control characters: {name!r}."
        )

    pure = PurePosixPath(name)
    if pure.is_absolute():
        raise package.ChallengePackageError(
            f"The ZIP contains an absolute path: {name!r}."
        )
    if any(part in ("", ".", "..") for part in pure.parts):
        raise package.ChallengePackageError(
            f"The ZIP contains a path traversal: {name!r}."
        )
    if ":" in name:
        raise package.ChallengePackageError(
            f"The ZIP contains a path with a colon: {name!r}."
        )
    for part in pure.parts:
        if part.endswith((" ", ".")):
            raise package.ChallengePackageError(
                f"The ZIP contains a path with a trailing space or dot: {name!r}."
            )
        stem = part.split(".", 1)[0].upper()
        if stem in WINDOWS_RESERVED_NAMES:
            raise package.ChallengePackageError(
                f"The ZIP contains a reserved filename: {name!r}."
            )


def _validate_archive_members(members):
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
            raise package.ChallengePackageError(
                f"The ZIP contains an encrypted file: {name!r}."
            )
        mode = info.external_attr >> 16
        if stat.S_ISLNK(mode):
            raise package.ChallengePackageError(
                f"The ZIP contains a symbolic link: {name!r}."
            )
        if info.is_dir():
            continue
        suffix = PurePosixPath(name).suffix.lower()
        if suffix not in ALLOWED_ARCHIVE_SUFFIXES:
            raise package.ChallengePackageError(
                f"The ZIP contains an unsupported file type: {name!r}."
            )
        casefolded = name.casefold()
        if casefolded in seen_names:
            raise package.ChallengePackageError(
                f"The ZIP contains a duplicate file: {name!r}."
            )
        seen_names.add(casefolded)
        file_count += 1
        if file_count > max_files:
            raise package.ChallengePackageError(
                f"The ZIP contains more than {max_files} files."
            )
        uncompressed_size += info.file_size
        if uncompressed_size > max_uncompressed:
            raise package.ChallengePackageError(
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
            raise package.ChallengePackageError(
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
                        raise package.ChallengePackageError(
                            "The ZIP expands beyond the allowed uncompressed size."
                        )
                    output.write(chunk)
        except package.ChallengePackageError:
            raise
        except (OSError, RuntimeError, NotImplementedError) as exc:
            raise package.ChallengePackageError(
                f"Could not extract {info.filename!r}: {exc}"
            ) from exc


def extract_challenge_archive(uploaded_file, destination):
    """Safely extract a ZIP and return its single package folder."""
    destination = Path(destination)
    try:
        uploaded_file.seek(0)
        if not zipfile.is_zipfile(uploaded_file):
            raise package.ChallengePackageError("Upload a valid .zip archive.")
        uploaded_file.seek(0)
        with zipfile.ZipFile(uploaded_file) as archive:
            members = [
                info
                for info in archive.infolist()
                if not _is_ignored_archive_member(info.filename)
            ]
            if not members:
                raise package.ChallengePackageError("The ZIP is empty.")
            _validate_archive_members(members)
            _extract_members(archive, members, destination)
    except package.ChallengePackageError:
        raise
    except (zipfile.BadZipFile, zipfile.LargeZipFile) as exc:
        raise package.ChallengePackageError("Upload a valid .zip archive.") from exc
    except (OSError, RuntimeError, NotImplementedError) as exc:
        raise package.ChallengePackageError(
            f"Could not read the ZIP archive: {exc}"
        ) from exc

    entries = [
        path
        for path in destination.iterdir()
        if not _is_ignored_archive_member(path.name)
    ]
    if len(entries) != 1 or not entries[0].is_dir():
        raise package.ChallengePackageError(
            "The ZIP must contain exactly one top-level challenge folder named after the slug."
        )
    return entries[0]


def import_challenge_archive(uploaded_file, *, replace=False, skip_existing=False):
    """Validate and install a ZIP package."""
    max_archive = _setting(
        "CHALLENGE_IMPORT_MAX_ARCHIVE_BYTES",
        DEFAULT_MAX_ARCHIVE_BYTES,
    )
    try:
        if _uploaded_file_size(uploaded_file) > max_archive:
            raise package.ChallengePackageError(
                f"The ZIP must be {max_archive // (1024 * 1024)} MB or smaller."
            )
        with tempfile.TemporaryDirectory(prefix="challenge-import-") as temporary:
            folder = extract_challenge_archive(uploaded_file, temporary)
            return import_challenge_package(
                folder,
                replace=replace,
                skip_existing=skip_existing,
            )
    except package.ChallengePackageError:
        raise
    except OSError as exc:
        raise package.ChallengePackageError(
            f"Could not read the challenge package: {exc}"
        ) from exc
