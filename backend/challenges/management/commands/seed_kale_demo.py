"""Load the bundled demo through the shared local-level importer."""

from django.core.management import call_command
from django.core.management.base import BaseCommand

DEMO_LEVEL_ID = "2026-10-15-forgot-password-x3"


class Command(BaseCommand):
    help = "Seed the 'Forgot Password x3' demo from its local level package."

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Replace the demo files and metadata, preserving its database ID.",
        )

    def handle(self, *args, **options):
        call_command(
            "import_levels", DEMO_LEVEL_ID, replace=options["force"], stdout=self.stdout
        )
