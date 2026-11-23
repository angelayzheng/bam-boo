"""Validate that challenge data and media are ready for production."""

from django.core.management.base import BaseCommand, CommandError

from config.container import get_container


class Command(BaseCommand):
    help = "Check that challenge data, source packages, and media are production-ready."

    def handle(self, *args, **options):
        try:
            use_case = get_container().build_validate_challenges_use_case()
            use_case.controller.execute()
        except CommandError:
            raise
        except Exception as exc:
            raise CommandError(f"Could not validate challenges: {exc}") from exc

        view_model = use_case.presenter.view_model
        if not view_model.success:
            for error in view_model.errors:
                self.stderr.write(f"ERROR: {error}")
            raise CommandError(view_model.message)

        self.stdout.write(view_model.message)
