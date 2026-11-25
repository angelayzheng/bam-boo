from django.core.exceptions import ValidationError
from django.core.validators import validate_email

from users.useCases.ports import EmailValidator


class DjangoEmailValidator(EmailValidator):
    def is_valid(self, email: str) -> bool:
        try:
            validate_email(email)
        except ValidationError:
            return False
        return True
