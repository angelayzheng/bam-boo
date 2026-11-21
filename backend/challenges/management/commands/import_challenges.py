"""Import local challenge packages without storing audio or transcripts in SQLite."""

from django.core.management.base import BaseCommand, CommandError

from config.container import get_container

from challenges import package


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

        use_case = get_container().build_import_challenge_package_use_case()
        use_case.controller.execute(
            sources=[available[slug] for slug in dict.fromkeys(requested)],
            replace=options["replace"],
            skip_existing=True,
        )
        view_model = use_case.presenter.view_model
        if not view_model.success:
            raise CommandError(view_model.message)

        for result in view_model.results:
            if result.skipped:
                self.stdout.write(
                    "Challenge already exists; use --replace to update it."
                )
                continue
            self.stdout.write(
                self.style.SUCCESS(
                    f"Imported {result.slug}: {result.name} "
                    f"({result.turn_count} turns)."
                )
            )
