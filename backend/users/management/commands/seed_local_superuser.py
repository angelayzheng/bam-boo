"""Create the shared development account during local setup."""

from getpass import getpass

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

DEFAULT_USERNAME = "admin"
DEFAULT_EMAIL = "admin@example.test"


class Command(BaseCommand):
    help = "Create a local-development superuser with a prompted password (requires DEBUG=True)."
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
            try:
                password = getpass("Password: ")
                confirmation = getpass("Password (again): ")
            except (EOFError, KeyboardInterrupt) as exc:
                raise CommandError(
                    "Password entry cancelled. No account was created."
                ) from exc
            if not password.strip():
                raise CommandError("Password cannot be blank. No account was created.")
            if password != confirmation:
                raise CommandError("Passwords do not match. No account was created.")
            try:
                validate_password(
                    password, User(username=DEFAULT_USERNAME, email=DEFAULT_EMAIL)
                )
            except ValidationError as exc:
                raise CommandError(" ".join(exc.messages)) from exc
            User.objects.create_superuser(
                username=DEFAULT_USERNAME,
                email=DEFAULT_EMAIL,
                password=password,
            )

        self.stdout.write(
            self.style.SUCCESS(f"Created local superuser '{DEFAULT_USERNAME}'.")
        )
