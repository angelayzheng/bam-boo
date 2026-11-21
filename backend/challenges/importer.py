"""Compatibility entry points for challenge imports.

The import rules live in the ``ImportChallengePackage`` use case. These helpers
keep the historical CLI/admin-facing function names while delegating to the
application container.
"""

from dataclasses import dataclass

from config.container import get_container

from .adapters.archives import (
    DEFAULT_MAX_ARCHIVE_BYTES,
    DEFAULT_MAX_FILES,
    DEFAULT_MAX_UNCOMPRESSED_BYTES,
    extract_challenge_archive,
)
from .domain.challenge_package import ChallengePackageError
from .models import Challenge


@dataclass(frozen=True)
class ImportResult:
    challenge: Challenge
    replaced: bool
    turn_count: int


def _execute(*, sources, replace, skip_existing):
    use_case = get_container().build_import_challenge_package_use_case()
    use_case.controller.execute(
        sources=sources,
        replace=replace,
        skip_existing=skip_existing,
    )
    view_model = use_case.presenter.view_model
    if not view_model.success:
        raise ChallengePackageError(view_model.message)
    return view_model.results


def import_challenge_package(folder, *, replace=False, skip_existing=False):
    """Validate and install one local package folder."""
    results = _execute(sources=[folder], replace=replace, skip_existing=skip_existing)
    if results[0].skipped:
        return None
    result = results[0]
    return ImportResult(
        challenge=Challenge.objects.get(slug=result.slug),
        replaced=result.replaced,
        turn_count=result.turn_count,
    )


def import_challenge_archive(uploaded_file, *, replace=False, skip_existing=False):
    """Validate and install one uploaded ZIP package."""
    results = _execute(
        sources=[uploaded_file], replace=replace, skip_existing=skip_existing
    )
    if results[0].skipped:
        return None
    result = results[0]
    return ImportResult(
        challenge=Challenge.objects.get(slug=result.slug),
        replaced=result.replaced,
        turn_count=result.turn_count,
    )


__all__ = [
    "DEFAULT_MAX_ARCHIVE_BYTES",
    "DEFAULT_MAX_FILES",
    "DEFAULT_MAX_UNCOMPRESSED_BYTES",
    "ChallengePackageError",
    "ImportResult",
    "extract_challenge_archive",
    "import_challenge_archive",
    "import_challenge_package",
]
