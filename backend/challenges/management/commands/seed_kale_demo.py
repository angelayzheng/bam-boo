"""Load the bundled demo through the shared local challenge importer."""

from django.core.management import call_command
from django.core.management.base import BaseCommand

DEMO_SLUG = "forgot-password-x3"


class Command(BaseCommand):
    help = "Seed the 'Forgot Password x3' demo from its local challenge package."

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Replace the demo files and metadata, preserving its database ID.",
        )

    def handle(self, *args, **options):
        call_command(
            "import_challenges", DEMO_SLUG, replace=options["force"], stdout=self.stdout
        )
