from datetime import date
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase

from .models import UserProfile


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
