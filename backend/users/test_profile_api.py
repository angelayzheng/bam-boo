import json

from django.contrib.auth.models import Group, User
from django.test import Client, TestCase


class UserByUsernameApiTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="ada")
        self.other = User.objects.create_user(username="grace")
        self.url = "/api/users/ada/"

    def test_get_returns_profile_schema(self):
        team = Group.objects.create(name="Alpha team")
        self.user.first_name = "Ada"
        self.user.last_name = "Lovelace"
        self.user.email = "ada@example.com"
        self.user.save()
        profile = self.user.profile
        profile.group = team
        profile.add_score("sample-challenge", 2)
        profile.login_days = ["2026-10-12", "2026-10-10"]
        profile.save()

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "slug": "ada",
                "challenge_scores": {"sample-challenge": 2},
                "total_score": 2.0,
                "name": "Ada Lovelace",
                "team": "alpha-team",
                "login_days": ["2026-10-10", "2026-10-12"],
                "avatar": "fox",
                "email": "ada@example.com",
            },
        )

    def test_get_unknown_username_returns_404(self):
        self.assertEqual(self.client.get("/api/users/missing/").status_code, 404)

    def test_post_requires_authentication_owner_and_csrf(self):
        anonymous = Client(enforce_csrf_checks=True)
        token = anonymous.get("/api/users/auth/csrf/").json()["csrfToken"]
        response = anonymous.post(
            self.url,
            data=json.dumps({"avatar": "owl"}),
            content_type="application/json",
            HTTP_X_CSRFTOKEN=token,
        )
        self.assertEqual(response.status_code, 401)

        other_client = Client(enforce_csrf_checks=True)
        other_client.force_login(self.other)
        token = other_client.get("/api/users/auth/csrf/").json()["csrfToken"]
        response = other_client.post(
            self.url,
            data=json.dumps({"avatar": "owl"}),
            content_type="application/json",
            HTTP_X_CSRFTOKEN=token,
        )
        self.assertEqual(response.status_code, 403)

        owner_client = Client(enforce_csrf_checks=True)
        owner_client.force_login(self.user)
        response = owner_client.post(
            self.url,
            data=json.dumps({"avatar": "owl"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 403)
        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.profile.avatar, "fox")

    def test_owner_can_update_profile_and_scores(self):
        team = Group.objects.create(name="Alpha team")
        client = Client()
        client.force_login(self.user)
        response = client.post(
            self.url,
            data=json.dumps(
                {
                    "slug": "ada",
                    "challenge_scores": {
                        "sample-challenge": 3,
                        "second-challenge": 1,
                    },
                    "name": "Ada Lovelace",
                    "team": "alpha-team",
                    "login_days": ["2026-10-12", "2026-10-10"],
                    "avatar": "owl",
                    "email": "ada@example.com",
                }
            ),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "slug": "ada",
                "challenge_scores": {
                    "sample-challenge": 3,
                    "second-challenge": 1,
                },
                "total_score": 4.0,
                "name": "Ada Lovelace",
                "team": "alpha-team",
                "login_days": ["2026-10-10", "2026-10-12"],
                "avatar": "owl",
                "email": "ada@example.com",
            },
        )
        self.user.refresh_from_db()
        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.first_name, "Ada Lovelace")
        self.assertEqual(self.user.email, "ada@example.com")
        self.assertEqual(self.user.profile.group, team)
        self.assertEqual(
            self.user.profile.scores,
            {"sample-challenge": 3, "second-challenge": 1},
        )
        self.assertEqual(self.user.profile.total_score, 4)

    def test_post_rejects_invalid_payloads_and_methods(self):
        client = Client()
        client.force_login(self.user)
        cases = (
            ("not-json", "application/json"),
            ("[]", "application/json"),
            ('{"avatar": "unicorn"}', "application/json"),
            ('{"challenge_scores": {"sample-challenge": 4}}', "application/json"),
            (
                '{"challenge_scores": {"sample-challenge": 1}, "total_score": 0}',
                "application/json",
            ),
            ('{"total_score": 100}', "application/json"),
            ('{"avatar": "owl"}', "text/plain"),
        )
        for body, content_type in cases:
            with self.subTest(body=body, content_type=content_type):
                response = client.post(self.url, data=body, content_type=content_type)
                self.assertEqual(response.status_code, 400)

        self.assertEqual(client.put(self.url).status_code, 405)
