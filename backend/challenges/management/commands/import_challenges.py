"""Import local challenge packages without storing audio or transcripts in SQLite."""

from django.core.management.base import BaseCommand, CommandError

from challenges.importer import (
    CHALLENGES_DIR,
    ChallengePackageError,
    install_challenge,
    prepare_challenge_package,
)


class Command(BaseCommand):
    help = "Import all local challenge packages, or only the specified slugs."

    def add_arguments(self, parser):
        parser.add_argument("slugs", nargs="*")
        parser.add_argument(
            "--replace",
            action="store_true",
            help="Replace existing challenges and their media, preserving database IDs.",
        )

    def handle(self, *args, **options):
        if not CHALLENGES_DIR.is_dir():
            raise CommandError(
                f"Challenge source directory not found: {CHALLENGES_DIR}"
            )
        available = {
            path.name: path for path in CHALLENGES_DIR.iterdir() if path.is_dir()
        }
        requested = options["slugs"] or sorted(available)
        missing = set(requested) - available.keys()
        if missing:
            raise CommandError(f"Unknown challenge slugs: {', '.join(sorted(missing))}")
        if not requested:
            raise CommandError(f"No challenge packages found in {CHALLENGES_DIR}.")
        try:
            prepared = [
                prepare_challenge_package(
                    available[slug],
                    replace=options["replace"],
                    skip_existing=True,
                )
                for slug in dict.fromkeys(requested)
            ]
        except ChallengePackageError as exc:
            raise CommandError(str(exc)) from exc
        for field in ("name", "slug"):
            seen = set()
            for package in prepared:
                if package is not None:
                    value = getattr(package.challenge, field)
                    if value in seen:
                        raise CommandError(
                            f"Selected challenges have a duplicate {field}: {value}"
                        )
                    seen.add(value)
        for package in prepared:
            if package is None:
                self.stdout.write(
                    "Challenge already exists; use --replace to update it."
                )
                continue
            try:
                install_challenge(package)
            except ChallengePackageError as exc:
                raise CommandError(str(exc)) from exc
            except OSError as exc:
                raise CommandError(
                    f"Could not install {package.challenge.slug}: {exc}"
                ) from exc
            self.stdout.write(
                self.style.SUCCESS(
                    f"Imported {package.challenge.slug}: "
                    f"{package.challenge.name} ({package.turn_count} turns)."
                )
            )
