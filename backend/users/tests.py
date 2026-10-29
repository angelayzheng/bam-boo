from datetime import date
from io import StringIO

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.core.management.base import CommandError
from django.contrib.sessions.models import Session
from django.test import Client, TestCase, override_settings

from .models import UserProfile


@override_settings(DEBUG=True)
class LocalSuperuserCommandTests(TestCase):
    def seed(self):
        output = StringIO()
        call_command("seed_local_superuser", stdout=output)
        return output.getvalue()

    def test_creates_default_superuser_and_profile_with_hashed_password(self):
        self.seed()
        user = User.objects.get(username="admin")
        self.assertEqual(user.email, "admin@example.test")
        self.assertTrue(user.is_active)
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.check_password("teamkale"))
        self.assertNotEqual(user.password, "teamkale")
        self.assertEqual(user.profile.avatar, "fox")

    def test_seeded_account_can_use_auth_api_and_admin(self):
        self.seed()
        client = Client(enforce_csrf_checks=True)
        token = client.get("/api/users/auth/csrf/").json()["csrfToken"]
        response = client.post(
            "/api/users/auth/login/",
            data={"username": "admin", "password": "teamkale"},
            content_type="application/json",
            HTTP_X_CSRFTOKEN=token,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["user"]["username"], "admin")
        self.assertEqual(client.get("/admin/").status_code, 200)

    def test_rerun_preserves_existing_password_and_profile(self):
        self.seed()
        user = User.objects.get(username="admin")
        user.set_password("ChangedLocalPassword!2026")
        user.email = "custom@example.test"
        user.save()
        profile = user.profile
        profile.avatar = "owl"
        profile.add_score("42", 80)
        profile.save()
        output = self.seed()
        user.refresh_from_db()
        profile.refresh_from_db()
        self.assertIn("already exists", output)
        self.assertTrue(user.check_password("ChangedLocalPassword!2026"))
        self.assertEqual(user.email, "custom@example.test")
        self.assertEqual(profile.avatar, "owl")
        self.assertEqual(profile.scores, {"42": 80})
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(UserProfile.objects.count(), 1)

    def test_conflicting_accounts_are_not_promoted_or_reactivated(self):
        for flags in (
            {},
            {"is_staff": True},
            {"is_staff": True, "is_superuser": True, "is_active": False},
        ):
            with self.subTest(flags=flags):
                user = User.objects.create_user(
                    username="admin", password="ExistingPassword!2026", **flags
                )
                with self.assertRaisesMessage(CommandError, "No account was changed"):
                    self.seed()
                user.refresh_from_db()
                self.assertTrue(user.check_password("ExistingPassword!2026"))
                self.assertEqual(user.is_superuser, flags.get("is_superuser", False))
                self.assertEqual(user.is_staff, flags.get("is_staff", False))
                self.assertEqual(user.is_active, flags.get("is_active", True))
                user.delete()

    @override_settings(DEBUG=False)
    def test_shared_account_is_not_created_outside_debug_mode(self):
        with self.assertRaisesMessage(CommandError, "requires DEBUG=True"):
            self.seed()
        self.assertFalse(User.objects.exists())


class AuthenticationApiTests(TestCase):
    password = "River!Quartz7Maple"
    base_url = "/api/users/auth/"

    def setUp(self):
        self.client = Client(enforce_csrf_checks=True)
        self.token = self.client.get(self.base_url + "csrf/").json()["csrfToken"]

    def post(self, action, payload=None, **extra):
        return self.client.post(
            self.base_url + action + "/",
            data=payload or {},
            content_type="application/json",
            HTTP_X_CSRFTOKEN=self.token,
            **extra,
        )

    def test_signup_creates_account_profile_and_session(self):
        response = self.post(
            "signup",
            {
                "username": "ada",
                "password": self.password,
                "email": "Ada@Example.COM",
                "is_superuser": True,
            },
            HTTP_ORIGIN="http://localhost:5173",
        )
        self.assertEqual(response.status_code, 201)
        user = User.objects.get(username="ada")
        self.assertTrue(user.check_password(self.password))
        self.assertFalse(user.is_superuser)
        self.assertEqual(user.email, "Ada@example.com")
        self.assertEqual(user.profile.avatar, "fox")
        self.assertEqual(self.client.session["_auth_user_id"], str(user.pk))
        payload = response.json()
        self.assertEqual(
            payload["user"],
            {"id": user.pk, "username": "ada", "email": "Ada@example.com"},
        )
        self.assertEqual(self.client.get(self.base_url + "me/").status_code, 200)
        self.assertIn("no-store", response.headers["Cache-Control"])
        # Signup rotates CSRF tokens; the returned token works immediately.
        self.token = payload["csrfToken"]
        self.assertEqual(self.post("logout").status_code, 200)

    def test_signup_email_is_optional(self):
        response = self.post("signup", {"username": "ada", "password": self.password})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(User.objects.get(username="ada").email, "")

    def test_signup_rejects_invalid_fields_without_creating_account(self):
        cases = [
            ({"username": "bad name", "password": self.password}, "username"),
            ({"username": "ada", "password": "password"}, "password"),
            ({"username": "ada", "password": "123456789"}, "password"),
            ({"username": "ada", "password": "short"}, "password"),
            (
                {"username": "ada", "password": self.password, "email": "invalid"},
                "email",
            ),
        ]
        for payload, field in cases:
            with self.subTest(payload=payload):
                response = self.post("signup", payload)
                self.assertEqual(response.status_code, 400)
                self.assertIn(field, response.json()["errors"])
        self.assertFalse(User.objects.exists())
        self.assertFalse(UserProfile.objects.exists())

    def test_signup_rejects_duplicate_username(self):
        User.objects.create_user(username="ada", password=self.password)
        for username in ("ada", "ADA"):
            with self.subTest(username=username):
                response = self.post(
                    "signup", {"username": username, "password": self.password}
                )
                self.assertEqual(response.status_code, 400)
                self.assertIn("username", response.json()["errors"])
        self.assertEqual(User.objects.count(), 1)

    def test_login_persists_identity_and_logout_invalidates_session(self):
        user = User.objects.create_user(username="ada", password=self.password)
        session = self.client.session
        session["anonymous_data"] = "retained"
        session.save()
        old_key = session.session_key
        response = self.post("login", {"username": "ada", "password": self.password})
        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(self.client.session.session_key, old_key)
        self.assertFalse(Session.objects.filter(session_key=old_key).exists())
        self.assertEqual(self.client.session["anonymous_data"], "retained")
        self.assertEqual(
            self.client.get(self.base_url + "me/").json()["user"]["id"], user.pk
        )
        user.refresh_from_db()
        self.assertIsNotNone(user.last_login)
        self.token = response.json()["csrfToken"]
        session_key = self.client.session.session_key
        self.assertEqual(self.post("logout").status_code, 200)
        self.assertFalse(Session.objects.filter(session_key=session_key).exists())
        self.assertEqual(self.client.get(self.base_url + "me/").status_code, 401)
        self.assertEqual(self.post("logout").status_code, 200)

    def test_login_rejects_invalid_credentials_and_inactive_accounts(self):
        User.objects.create_user(username="ada", password=self.password)
        User.objects.create_user(
            username="inactive", password=self.password, is_active=False
        )
        for username, password in (
            ("ada", "wrong"),
            ("unknown", self.password),
            ("inactive", self.password),
        ):
            with self.subTest(username=username):
                response = self.post(
                    "login", {"username": username, "password": password}
                )
                self.assertEqual(response.status_code, 401)
                self.assertEqual(
                    response.json()["detail"], "Invalid username or password."
                )
                self.assertNotIn("_auth_user_id", self.client.session)

    def test_signup_and_login_reject_malformed_payloads(self):
        bodies = ["{", "[]", "null", '"text"', "{}", b"\xff"]
        for action in ("signup", "login"):
            for body in bodies:
                with self.subTest(action=action, body=body):
                    response = self.client.post(
                        self.base_url + action + "/",
                        data=body,
                        content_type="application/json",
                        HTTP_X_CSRFTOKEN=self.token,
                    )
                    self.assertEqual(response.status_code, 400)
            for field in ("username", "password", "email"):
                for value in (None, 12, [], {}):
                    with self.subTest(action=action, field=field, value=value):
                        payload = {"username": "ada", "password": self.password}
                        payload[field] = value
                        self.assertEqual(self.post(action, payload).status_code, 400)
            response = self.client.post(
                self.base_url + action + "/",
                data={"username": "ada", "password": self.password},
                HTTP_X_CSRFTOKEN=self.token,
            )
            self.assertEqual(response.status_code, 400)

    def test_authentication_posts_require_csrf_and_trusted_origin(self):
        for action in ("signup", "login", "logout"):
            url = self.base_url + action + "/"
            with self.subTest(action=action):
                self.assertEqual(self.client.post(url).status_code, 403)
                self.assertEqual(
                    self.client.post(url, HTTP_X_CSRFTOKEN="invalid").status_code,
                    403,
                )
                self.assertEqual(
                    self.post(
                        action, HTTP_ORIGIN="https://untrusted.example"
                    ).status_code,
                    403,
                )

    def test_anonymous_current_user_and_http_methods(self):
        self.assertEqual(self.client.get(self.base_url + "me/").status_code, 401)
        for action in ("signup", "login", "logout"):
            self.assertEqual(
                self.client.get(self.base_url + action + "/").status_code, 405
            )
        for action in ("csrf", "me"):
            self.assertEqual(self.post(action).status_code, 405)


class UserProfileModelTests(TestCase):
    def test_profile_auto_created_with_defaults(self):
        user = User.objects.create_user(
            username="ada", email="Ada@Example.com", password="s3cure-pass"
        )
        profile = UserProfile.objects.get(user=user)
        self.assertEqual(profile.avatar, "fox")
        self.assertEqual(profile.scores, {})
        self.assertEqual(profile.total_score, 0)
        self.assertEqual(profile.login_days, [])

    def test_email_is_normalized(self):
        user = User.objects.create_user(
            username="grace", email="Grace@Example.COM", password="s3cure-pass"
        )
        self.assertEqual(user.email, "Grace@example.com")

    def test_password_uses_django_hashing(self):
        user = User.objects.create_user(username="lin", password="s3cure-pass")
        self.assertNotEqual(user.password, "s3cure-pass")
        self.assertTrue(user.check_password("s3cure-pass"))

    def test_add_score_updates_total(self):
        user = User.objects.create_user(username="ada", password="s3cure-pass")
        profile = user.profile
        profile.add_score(1, 80)
        profile.add_score(2, 70)
        profile.save()
        profile.refresh_from_db()
        self.assertEqual(profile.scores, {"1": 80.0, "2": 70.0})
        self.assertEqual(profile.total_score, 150.0)

    def test_add_score_rejects_out_of_range(self):
        user = User.objects.create_user(username="ada", password="s3cure-pass")
        with self.assertRaises(ValidationError):
            user.profile.add_score(1, 101)

    def test_scores_validator_rejects_non_numeric(self):
        user = User.objects.create_user(username="ada", password="s3cure-pass")
        profile = user.profile
        profile.scores = {"1": "high"}
        with self.assertRaises(ValidationError):
            profile.save()

    def test_record_login_appends_sorted_unique_days(self):
        user = User.objects.create_user(username="ada", password="s3cure-pass")
        profile = user.profile
        profile.record_login(date(2026, 10, 14))
        profile.record_login(date(2026, 10, 14))
        profile.record_login(date(2026, 10, 12))
        profile.save()
        profile.refresh_from_db()
        self.assertEqual(profile.login_days, ["2026-10-12", "2026-10-14"])

    def test_login_days_validator_rejects_bad_format(self):
        user = User.objects.create_user(username="ada", password="s3cure-pass")
        profile = user.profile
        profile.login_days = ["14-10-2026"]
        with self.assertRaises(ValidationError):
            profile.save()


class UserProfileApiTests(TestCase):
    def test_profile_endpoint(self):
        user = User.objects.create_user(username="ada", password="s3cure-pass")
        profile = user.profile
        profile.add_score(1, 90)
        profile.save()

        response = self.client.get(f"/api/users/{user.id}/profile/")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["username"], "ada")
        self.assertEqual(payload["total_score"], 90.0)
        self.assertEqual(payload["completed_challenges"], 1)

    def test_profile_endpoint_404(self):
        response = self.client.get("/api/users/9999/profile/")
        self.assertEqual(response.status_code, 404)

    def test_profile_endpoint_hides_private_fields(self):
        user = User.objects.create_user(
            username="ada", email="ada@example.com", password="s3cure-pass"
        )
        payload = self.client.get(f"/api/users/{user.id}/profile/").json()
        self.assertNotIn("email", payload)
        self.assertNotIn("password", payload)
        self.assertNotIn("login_days", payload)

    def test_leaderboard_orders_by_total_score(self):
        low = User.objects.create_user(username="low", password="s3cure-pass")
        high = User.objects.create_user(username="high", password="s3cure-pass")
        low.profile.add_score(1, 10)
        low.profile.save()
        high.profile.add_score(1, 95)
        high.profile.save()

        payload = self.client.get("/api/users/leaderboard/").json()
        self.assertEqual(payload["leaderboard"][0]["username"], "high")
        self.assertEqual(payload["leaderboard"][1]["username"], "low")
