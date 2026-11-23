import logging
import shutil
import tempfile
import threading
from collections.abc import Sequence
from contextlib import ExitStack, contextmanager
from pathlib import Path

from django.conf import settings

from challenges import package as package_module
from challenges.domain.ChallengePackage import ChallengePackageError
from challenges.use_cases.ports import MediaStore, PreparedChallengePackage

logger = logging.getLogger(__name__)

_IMPORT_LOCK = threading.Lock()


def _remove_path(path):
    if path.is_dir() and not path.is_symlink():
        shutil.rmtree(path)
    elif path.exists() or path.is_symlink():
        path.unlink()


@contextmanager
def _import_lock(media_root):
    try:
        import fcntl
    except ImportError:
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


def _stage_package(source, parent, slug):
    temporary = tempfile.TemporaryDirectory(prefix=".import-", dir=parent)
    staged = Path(temporary.name) / "new"
    staged.mkdir()
    try:
        shutil.copyfile(
            source.folder / f"{source.folder.name}.json",
            staged / f"{slug}.json",
        )
        for relative in source.files:
            target = staged / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source.folder / relative, target)
    except Exception:
        temporary.cleanup()
        raise
    return temporary, staged


def _published_source_destination(source):
    return Path(package_module.CHALLENGES_DIR) / source.slug


def _needs_source_install(source):
    destination = _published_source_destination(source)
    return source.folder.resolve() != destination.resolve()


class FileSystemMediaStore(MediaStore):
    def install(
        self, packages: Sequence[PreparedChallengePackage], *, replace: bool
    ) -> None:
        media_root = Path(settings.MEDIA_ROOT) / "challenges"
        source_root = Path(package_module.CHALLENGES_DIR)

        try:
            media_root.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise ChallengePackageError(
                f"Could not stage challenge files: {exc}"
            ) from exc

        with ExitStack() as stack:
            staged = []
            try:
                for item in packages:
                    source = item.source
                    media_temporary, media_staged = _stage_package(
                        source, media_root, item.challenge.slug
                    )
                    stack.callback(media_temporary.cleanup)

                    install_source = _needs_source_install(source)
                    source_temporary = None
                    source_staged = None
                    if install_source:
                        source_root.mkdir(parents=True, exist_ok=True)
                        source_temporary, source_staged = _stage_package(
                            source, source_root, item.challenge.slug
                        )
                        stack.callback(source_temporary.cleanup)
                    staged.append(
                        (
                            item,
                            media_temporary,
                            media_staged,
                            source_temporary,
                            source_staged,
                        )
                    )
            except OSError as exc:
                raise ChallengePackageError(
                    f"Could not stage challenge files: {exc}"
                ) from exc

            with _import_lock(media_root):
                backups: list[tuple[Path, Path]] = []
                installed: list[Path] = []
                try:
                    for item, media_temporary, _, source_temporary, _ in staged:
                        media_destination = media_root / item.challenge.slug
                        if media_destination.exists():
                            backup = Path(media_temporary.name) / "previous"
                            media_destination.rename(backup)
                            backups.append((media_destination, backup))
                        if source_temporary is not None:
                            source_destination = source_root / item.challenge.slug
                            if source_destination.exists():
                                backup = Path(source_temporary.name) / "previous"
                                source_destination.rename(backup)
                                backups.append((source_destination, backup))

                    for item, _, media_staged, _, source_staged in staged:
                        media_destination = media_root / item.challenge.slug
                        media_staged.rename(media_destination)
                        installed.append(media_destination)
                        if source_staged is not None:
                            source_destination = source_root / item.challenge.slug
                            source_staged.rename(source_destination)
                            installed.append(source_destination)
                except Exception as exc:
                    for path in reversed(installed):
                        _remove_path(path)
                    for destination, backup in reversed(backups):
                        if backup.exists():
                            backup.rename(destination)
                    raise ChallengePackageError(
                        f"Could not save challenge files: {exc}"
                    ) from exc

        for item in packages:
            logger.info(
                "Installed challenge package %s with %s turns.",
                item.challenge.slug,
                item.source.turn_count,
            )
