"""Import local challenge packages without storing audio or transcripts in SQLite."""

from django.core.management.base import BaseCommand, CommandError

from challenges import package
from challenges.importer import install_challenge, prepare_challenge_package


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
        challenges_dir = package.CHALLENGES_DIR
        if not challenges_dir.is_dir():
            raise CommandError(
                f"Challenge source directory not found: {challenges_dir}"
            )
        available = {
            path.name: path
            for path in challenges_dir.iterdir()
            if path.is_dir() and not path.name.startswith(".")
        }
        requested = options["slugs"] or sorted(available)
        missing = set(requested) - available.keys()
        if missing:
            raise CommandError(f"Unknown challenge slugs: {', '.join(sorted(missing))}")
        if not requested:
            raise CommandError(f"No challenge packages found in {challenges_dir}.")
        try:
            prepared = [
                prepare_challenge_package(
                    available[slug],
                    replace=options["replace"],
                    skip_existing=True,
                )
                for slug in dict.fromkeys(requested)
            ]
        except package.ChallengePackageError as exc:
            raise CommandError(str(exc)) from exc
        for field in ("name", "slug"):
            seen = set()
            for challenge_package in prepared:
                if challenge_package is not None:
                    value = getattr(challenge_package.challenge, field)
                    if value in seen:
                        raise CommandError(
                            f"Selected challenges have a duplicate {field}: {value}"
                        )
                    seen.add(value)
        for challenge_package in prepared:
            if challenge_package is None:
                self.stdout.write(
                    "Challenge already exists; use --replace to update it."
                )
                continue
            try:
                install_challenge(challenge_package)
            except package.ChallengePackageError as exc:
                raise CommandError(
                    f"Could not install {challenge_package.challenge.slug}: {exc}"
                ) from exc
            self.stdout.write(
                self.style.SUCCESS(
                    f"Imported {challenge_package.challenge.slug}: "
                    f"{challenge_package.challenge.name} "
                    f"({challenge_package.turn_count} turns)."
                )
            )
