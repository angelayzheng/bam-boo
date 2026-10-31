"""Validate that challenge data and media are ready for production."""

from django.core.management.base import BaseCommand, CommandError

from challenges.validation import ChallengeDatabaseValidator


class Command(BaseCommand):
    help = "Check that challenge data, source packages, and media are production-ready."

    def handle(self, *args, **options):
        try:
            errors = ChallengeDatabaseValidator().validate()
        except Exception as exc:
            raise CommandError(f"Could not validate challenges: {exc}") from exc

        if errors:
            for error in errors:
                self.stderr.write(f"ERROR: {error}")
            raise CommandError("Challenge validation failed.")
        self.stdout.write("OK")
