from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError, transaction

from users.forms import SignupForm
from users.useCases.ports import (
    AccountCreationResult,
    AuthenticatedAccount,
    AuthenticationGateway,
)


class DjangoAuthenticationGateway(AuthenticationGateway):
    """Django account, credential, and session operations for auth use cases."""

    def __init__(self, request):
        self._request = request
        self._session_user = None

    @staticmethod
    def _account(user) -> AuthenticatedAccount:
        return AuthenticatedAccount(
            user_id=user.pk, username=user.username, email=user.email
        )

    def create_account(
        self, *, username: str, password: str, email: str, group_id: int | None
    ) -> AccountCreationResult:
        form = SignupForm(
            data={
                "username": username,
                "email": email,
                "group_id": group_id,
                "password1": password,
                "password2": password,
            }
        )
        if not form.is_valid():
            errors = {}
            for field, messages in form.errors.items():
                key = "password" if field in ("password1", "password2") else field
                errors.setdefault(key, []).extend(messages)
            return AccountCreationResult(account=None, errors=errors)
        try:
            with transaction.atomic():
                user = form.save()
                self._session_user = user
                if form.cleaned_data["group_id"] is not None:
                    profile = user.profile
                    profile.group = form.cleaned_data["group_id"]
                    profile.save(update_fields=["group", "updated_at"])
        except IntegrityError:
            return AccountCreationResult(
                account=None,
                errors={"username": ["A user with that username already exists."]},
            )
        return AccountCreationResult(account=self._account(user), errors={})

    def authenticate(
        self, *, username: str, password: str
    ) -> AuthenticatedAccount | None:
        user = authenticate(self._request, username=username, password=password)
        self._session_user = user
        return self._account(user) if user is not None else None

    def start_session(self, account: AuthenticatedAccount) -> None:
        if self._session_user is None or self._session_user.pk != account.user_id:
            raise RuntimeError("No matching authenticated user is available.")
        login(self._request, self._session_user)

    def end_session(self) -> None:
        logout(self._request)
