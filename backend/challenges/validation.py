"""Read-only production-readiness validation for challenge data."""

import hashlib
import mimetypes
import os
from pathlib import Path
from urllib.parse import urlsplit

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import RequestFactory
from django.urls import Resolver404, resolve

from . import package
from .models import Challenge
from .serialization import media_url

DEFAULT_MIME_TYPES = {
    "audio_file": "audio/mpeg",
    "transcript_file": "text/plain",
}


class ChallengeDatabaseValidator:
    """Validate that challenge rows can be served and match their sources."""

    def __init__(self, *, media_root=None, source_root=None):
        self.media_root = Path(media_root or settings.MEDIA_ROOT)
        self.source_root = Path(source_root or package.CHALLENGES_DIR)

    def validate(self):
        errors = self._database_errors()
        errors.extend(self._environment_errors())
        if errors:
            return errors
        for challenge in Challenge.objects.all().order_by("slug"):
            errors.extend(self._challenge_errors(challenge))
        return errors

    def _database_errors(self):
        errors = []
        try:
            if connection.vendor == "sqlite":
                with connection.cursor() as cursor:
                    cursor.execute("PRAGMA integrity_check")
                    integrity = [row[0] for row in cursor.fetchall()]
                    if integrity != ["ok"]:
                        errors.append(
                            "SQLite integrity_check failed: "
                            + "; ".join(str(value) for value in integrity)
                        )
                    cursor.execute("PRAGMA foreign_key_check")
                    if cursor.fetchall():
                        errors.append(
                            "SQLite foreign_key_check found foreign key violations."
                        )
            executor = MigrationExecutor(connection)
            plan = executor.migration_plan(executor.loader.graph.leaf_nodes())
            if plan:
                migrations = ", ".join(
                    f"{migration.app_label}.{migration.name}"
                    for migration, _backwards in plan
                )
                errors.append(f"Unapplied migrations: {migrations}.")
        except Exception as exc:
            errors.append(f"Could not inspect the database: {exc}")
        return errors

    def _environment_errors(self):
        errors = []
        if not self.media_root.is_dir():
            errors.append(f"MEDIA_ROOT is not a directory: {self.media_root}.")
        if not self.source_root.is_dir():
            errors.append(
                f"Challenge source root is not a directory: {self.source_root}."
            )
        if not settings.MEDIA_URL or not settings.MEDIA_URL.endswith("/"):
            errors.append("MEDIA_URL must be a nonempty value ending in '/'.")
        return errors

    def _challenge_errors(self, challenge):
        slug = challenge.slug
        try:
            challenge.full_clean()
        except ValidationError as exc:
            return [f"{slug}: invalid challenge row: {'; '.join(exc.messages)}"]
        if not challenge.conversation_tree:
            return [f"{slug}: conversation tree is empty."]
        errors = self._tree_errors(challenge)
        errors.extend(self._source_errors(challenge))
        return errors

    def _tree_errors(self, challenge):
        errors = []
        for node in package.iter_conversation_nodes(challenge.conversation_tree):
            key = node["node_key"]
            slug = challenge.slug
            for field, directory, suffix, mime_key in (
                ("text_file", "transcripts", ".txt", "transcript_file"),
                ("audio_file", "audio", ".mp3", "audio_file"),
            ):
                expected = f"challenges/{slug}/{directory}/{key}{suffix}"
                stored = node[field]
                label = f"{slug}: {key} {field}"
                if stored != expected:
                    errors.append(
                        f"{label}: stored path must be {expected!r}, got {stored!r}."
                    )
                    continue
                errors.extend(
                    self._media_errors(stored, DEFAULT_MIME_TYPES[mime_key], label)
                )
        return errors

    def _media_errors(self, stored_path, expected_mime, label):
        errors = []
        media_root = self.media_root.resolve()
        relative = Path(stored_path)
        if relative.is_absolute() or ".." in relative.parts:
            return [f"{label}: path is not a safe relative media path."]
        path = self.media_root / relative
        try:
            resolved = path.resolve()
        except OSError as exc:
            return [f"{label}: could not resolve media path: {exc}."]
        if not resolved.is_relative_to(media_root):
            return [f"{label}: media path resolves outside MEDIA_ROOT."]
        if path.is_symlink():
            errors.append(f"{label}: media file must not be a symbolic link.")
        if not path.is_file():
            return [*errors, f"{label}: media file is missing."]
        try:
            if path.stat().st_size <= 0:
                errors.append(f"{label}: media file is empty.")
        except OSError as exc:
            return [*errors, f"{label}: could not stat media file: {exc}."]
        if not os.access(path, os.R_OK):
            errors.append(f"{label}: media file is not readable.")
        detected_mime = mimetypes.guess_type(path.name)[0]
        if detected_mime != expected_mime:
            errors.append(
                f"{label}: expected media type {expected_mime!r}, "
                f"found {detected_mime!r}."
            )
        if expected_mime == "text/plain":
            try:
                content = path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError) as exc:
                errors.append(f"{label}: transcript is not valid UTF-8: {exc}.")
            else:
                if not content.strip():
                    errors.append(f"{label}: transcript is blank.")
        if errors:
            return errors
        return self._retrieval_errors(stored_path, expected_mime, label)

    def _retrieval_errors(self, stored_path, expected_mime, label):
        """Check that the generated URL is served when a local route exists."""
        media_prefix = urlsplit(settings.MEDIA_URL).path
        url = media_url(stored_path)
        url_path = urlsplit(url).path
        if not url_path.startswith(media_prefix):
            return [f"{label}: generated URL {url!r} is outside MEDIA_URL."]
        relative_url_path = url_path[len(media_prefix) :]
        if relative_url_path != stored_path:
            return [f"{label}: generated URL {url!r} does not map to the stored path."]

        request_path = "/" + url_path.lstrip("/")
        try:
            match = resolve(request_path)
        except Resolver404:
            return []
        except Exception as exc:
            return [f"{label}: could not resolve media URL: {exc}."]

        try:
            request = RequestFactory().get(request_path)
            response = match.func(request, *match.args, **match.kwargs)
        except Exception as exc:
            return [f"{label}: could not retrieve media URL: {exc}."]
        errors = []
        try:
            if response.status_code != 200:
                errors.append(
                    f"{label}: media URL returned HTTP {response.status_code}."
                )
                return errors
            content_length = response.get("Content-Length")
            try:
                length = int(content_length)
            except TypeError, ValueError:
                length = 0
            if length <= 0:
                errors.append(f"{label}: media URL has no positive Content-Length.")
            content_type = (response.get("Content-Type") or "").split(";", 1)[0]
            if content_type.strip() != expected_mime:
                errors.append(
                    f"{label}: media URL returned content type "
                    f"{content_type.strip()!r}, expected {expected_mime!r}."
                )
        finally:
            close = getattr(response, "close", None)
            if close is not None:
                close()
        return errors

    def _source_errors(self, challenge):
        slug = challenge.slug
        source_folder = self.source_root / slug
        if not source_folder.is_dir():
            return [f"{slug}: source package folder is missing."]
        try:
            source_package = package.load_challenge_package(source_folder)
        except package.ChallengePackageError as exc:
            return [f"{slug}: invalid source package: {exc}"]

        errors = []
        expected_metadata = {
            "name": challenge.name,
            "slug": challenge.slug,
            "challenge_date": challenge.challenge_date.isoformat(),
            "difficulty": challenge.difficulty,
            "category": challenge.category,
            "tone": challenge.tone,
            "required_action": challenge.required_action,
        }
        for field in package.METADATA_FIELDS:
            if source_package.metadata.get(field) != expected_metadata[field]:
                errors.append(
                    f"{slug}: source metadata {field!r} differs from the database."
                )
        if source_package.conversation_tree != challenge.conversation_tree:
            errors.append(
                f"{slug}: source conversation tree differs from the database."
            )

        media_folder = self.media_root / "challenges" / slug
        for relative in sorted(source_package.files):
            source_path = source_folder / relative
            media_path = media_folder / relative
            if not media_path.is_file():
                errors.append(
                    f"{slug}: source file has no published media copy: {relative}."
                )
                continue
            try:
                source_hash = _sha256(source_path)
                media_hash = _sha256(media_path)
            except OSError as exc:
                errors.append(
                    f"{slug}: could not read source or media file "
                    f"{relative}: {exc}."
                )
                continue
            if source_hash != media_hash:
                errors.append(f"{slug}: source and published media differ: {relative}.")
        return errors


def _sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as source:
        while True:
            chunk = source.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.digest()
