"""Create the shared development account during local setup."""

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

DEFAULT_USERNAME = "admin"
DEFAULT_EMAIL = "admin@example.test"
DEFAULT_PASSWORD = "teamkale"


class Command(BaseCommand):
    help = "Create the shared local-development superuser (requires DEBUG=True)."
    requires_migrations_checks = True

    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError("The shared local superuser requires DEBUG=True.")

        User = get_user_model()
        with transaction.atomic():
            user = User.objects.filter(username=DEFAULT_USERNAME).first()
            if user is not None:
                if not (user.is_superuser and user.is_staff and user.is_active):
                    raise CommandError(
                        f"Username '{DEFAULT_USERNAME}' is already used by an account "
                        "that is not an active superuser. Rename that account before "
                        "running this command. No account was changed."
                    )
                self.stdout.write(
                    f"Local superuser '{DEFAULT_USERNAME}' already exists; "
                    "its password and profile were left unchanged."
                )
                return
            User.objects.create_superuser(
                username=DEFAULT_USERNAME,
                email=DEFAULT_EMAIL,
                password=DEFAULT_PASSWORD,
            )

        self.stdout.write(
            self.style.SUCCESS(f"Created local superuser '{DEFAULT_USERNAME}'.")
        )
