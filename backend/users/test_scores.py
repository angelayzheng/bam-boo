from uuid import uuid4

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from challenges.models import Challenge

from .models import ChallengeAttempt, UserProfile


class ChallengeScoreApiTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username="ada", password="Score!Maple7River"
        )
        cls.other = User.objects.create_user(
            username="grace", password="Other!Maple7River"
        )
        cls.challenge = Challenge.objects.create(
            name="Score challenge",
            slug="score-challenge",
            challenge_date="2026-10-15",
            difficulty=2,
            category="social",
            tone="calm",
            required_action="reset password",
        )
        cls.second = Challenge.objects.create(
            name="Second score challenge",
            slug="second-score-challenge",
            challenge_date="2026-10-16",
            difficulty=2,
            category="social",
            tone="calm",
            required_action="reset password",
        )

    def setUp(self):
        self.client = Client(enforce_csrf_checks=True)
        self.client.force_login(self.user)
        self.token = self.client.get("/api/users/auth/csrf/").json()["csrfToken"]
        self.url = f"/api/users/me/scores/{self.challenge.pk}/"

    def post(self, payload, url=None):
        return self.client.post(
            url or self.url,
            data={
                "attempt_id": str(uuid4()),
                "completed_at": "2026-10-29T01:23:45Z",
                **payload,
            },
            content_type="application/json",
            HTTP_X_CSRFTOKEN=self.token,
        )

    def test_score_matches_the_three_result_stars(self):
        for tone, seconds, action, expected in (
            (False, 11, False, 0),
            (True, 11, False, 1),
            (False, 10, False, 1),
            (True, 10, False, 2),
            (True, 10, True, 3),
        ):
            with self.subTest(tone=tone, seconds=seconds, action=action):
                UserProfile.objects.filter(user=self.user).update(
                    scores={}, total_score=0
                )
                response = self.post(
                    {
                        "tone_correct": tone,
                        "tone_time": seconds,
                        "action_correct": action,
                    }
                )
                self.assertEqual(response.status_code, 201)
                self.assertEqual(
                    response.json()["scores"], {str(self.challenge.pk): expected}
                )
                self.assertEqual(response.json()["completed_challenges"], 1)
                self.assertEqual(response.json()["total_score"], expected)
                profile = UserProfile.objects.get(user=self.user)
                self.assertEqual(profile.scores, {str(self.challenge.pk): expected})
                self.assertEqual(profile.total_score, expected)
                self.assertIn("no-store", response.headers["Cache-Control"])

    def test_repeats_keep_best_scores_without_inflating_totals(self):
        one_star = {"tone_correct": True, "tone_time": 11, "action_correct": False}
        two_stars = {**one_star, "tone_time": 10}
        three_stars = {**two_stars, "action_correct": True}
        for _ in range(2):
            self.assertEqual(self.post(one_star).json()["total_score"], 1)
        second_url = f"/api/users/me/scores/{self.second.pk}/"
        self.assertEqual(self.post(two_stars, second_url).json()["total_score"], 3)
        self.assertEqual(self.post(three_stars).json()["total_score"], 5)
        repeated = self.post(one_star).json()
        self.assertEqual(repeated["total_score"], 5)
        self.assertEqual(repeated["completed_challenges"], 2)
        self.assertEqual(
            repeated["scores"],
            {str(self.challenge.pk): 3, str(self.second.pk): 2},
        )
        profile = self.client.get(f"/api/users/{self.user.pk}/profile/").json()
        self.assertEqual(
            profile, {key: value for key, value in repeated.items() if key != "attempt"}
        )
        self.assertEqual(
            ChallengeAttempt.objects.filter(profile__user=self.user).count(), 5
        )
        self.assertEqual(
            list(
                ChallengeAttempt.objects.filter(profile__user=self.user)
                .order_by("received_at")
                .values_list("score", flat=True)
            ),
            [1, 1, 2, 3, 1],
        )
        leaderboard = self.client.get("/api/users/leaderboard/").json()["leaderboard"]
        self.assertEqual(leaderboard[0]["user_id"], self.user.pk)
        self.assertEqual(leaderboard[0]["total_score"], 5)

    def test_session_identity_and_server_calculation_ignore_forged_fields(self):
        response = self.post(
            {
                "tone_correct": False,
                "tone_time": 20,
                "action_correct": False,
                "user_id": self.other.pk,
                "username": self.other.username,
                "score": 100,
                "total_score": 1000,
            }
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["user_id"], self.user.pk)
        self.assertEqual(response.json()["total_score"], 0)
        self.assertEqual(UserProfile.objects.get(user=self.other).scores, {})

    def test_requires_authentication_csrf_and_post(self):
        self.assertEqual(self.client.get(self.url).status_code, 405)
        self.assertEqual(self.client.post(self.url).status_code, 403)
        self.assertEqual(
            self.client.post(
                self.url,
                HTTP_X_CSRFTOKEN=self.token,
                HTTP_ORIGIN="https://untrusted.example",
            ).status_code,
            403,
        )
        self.client.logout()
        self.token = self.client.get("/api/users/auth/csrf/").json()["csrfToken"]
        self.assertEqual(self.post({}).status_code, 401)

    def test_attempt_keeps_challenge_id_and_original_completion_time(self):
        completed_at = "2026-10-28T23:15:43-04:00"
        before = timezone.now()
        response = self.post(
            {
                "tone_correct": True,
                "tone_time": 8,
                "action_correct": False,
                "completed_at": completed_at,
            }
        )
        self.assertEqual(response.status_code, 201)
        attempt = ChallengeAttempt.objects.get()
        self.assertEqual(attempt.challenge_id, self.challenge.pk)
        self.assertEqual(attempt.completed_at, parse_datetime(completed_at))
        self.assertGreaterEqual(attempt.received_at, before)
        self.assertLessEqual(attempt.received_at, timezone.now())
        self.assertEqual(response.json()["attempt"]["challenge_id"], self.challenge.pk)
        self.assertEqual(
            parse_datetime(response.json()["attempt"]["completed_at"]),
            attempt.completed_at,
        )

    def test_retries_reuse_attempt_but_a_new_completion_creates_history(self):
        payload = {
            "tone_correct": True,
            "tone_time": 8,
            "action_correct": True,
            "attempt_id": str(uuid4()),
        }
        self.assertEqual(self.post(payload).status_code, 201)
        self.assertEqual(self.post(payload).status_code, 200)
        self.assertEqual(ChallengeAttempt.objects.count(), 1)
        self.assertEqual(
            self.post({**payload, "action_correct": False}).status_code, 409
        )
        self.assertEqual(ChallengeAttempt.objects.count(), 1)
        payload["attempt_id"] = str(uuid4())
        self.assertEqual(
            self.post({**payload, "action_correct": False}).status_code, 201
        )
        self.assertEqual(ChallengeAttempt.objects.count(), 2)
        self.assertEqual(
            UserProfile.objects.get(user=self.user).scores[str(self.challenge.pk)],
            3,
        )

    def test_attempt_id_cannot_be_reused_for_another_user_or_challenge(self):
        payload = {
            "tone_correct": True,
            "tone_time": 8,
            "action_correct": True,
            "attempt_id": str(uuid4()),
        }
        self.assertEqual(self.post(payload).status_code, 201)
        self.assertEqual(
            self.post(payload, f"/api/users/me/scores/{self.second.pk}/").status_code,
            409,
        )
        self.client.force_login(self.other)
        self.token = self.client.get("/api/users/auth/csrf/").json()["csrfToken"]
        self.assertEqual(self.post(payload).status_code, 409)
        self.assertEqual(ChallengeAttempt.objects.count(), 1)
        self.assertEqual(UserProfile.objects.get(user=self.other).scores, {})

    def test_rejects_invalid_attempt_ids_and_naive_or_invalid_dates(self):
        valid = {"tone_correct": True, "tone_time": 4, "action_correct": True}
        for field, values in (
            ("attempt_id", [None, 1, "invalid", {}, []]),
            (
                "completed_at",
                [
                    None,
                    1,
                    "invalid",
                    "2026-10-29",
                    "2026-10-29T12:00:00",
                    "2026-99-99T12:00:00Z",
                ],
            ),
        ):
            for value in values:
                with self.subTest(field=field, value=value):
                    self.assertEqual(
                        self.post({**valid, field: value}).status_code, 400
                    )
        self.assertEqual(ChallengeAttempt.objects.count(), 0)
        self.assertEqual(
            self.post(valid, "/api/users/me/scores/not-a-number/").status_code,
            404,
        )

    def test_rejects_missing_challenge_without_changing_scores(self):
        response = self.post(
            {"tone_correct": True, "tone_time": 4, "action_correct": True},
            "/api/users/me/scores/999999/",
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["detail"], "Challenge not found.")
        self.assertEqual(UserProfile.objects.get(user=self.user).scores, {})

    def test_rejects_invalid_result_fields_without_changing_scores(self):
        valid = {"tone_correct": True, "tone_time": 4, "action_correct": True}
        for field, invalid_values in (
            ("tone_correct", [None, 1, "true", [], {}]),
            ("action_correct", [None, 0, "false", [], {}]),
            ("tone_time", [None, True, -1, "4", [], {}, float("nan"), float("inf")]),
        ):
            for value in invalid_values:
                with self.subTest(field=field, value=value):
                    self.assertEqual(
                        self.post({**valid, field: value}).status_code, 400
                    )
            missing = {key: value for key, value in valid.items() if key != field}
            self.assertEqual(self.post(missing).status_code, 400)
        self.assertEqual(UserProfile.objects.get(user=self.user).scores, {})

    def test_rejects_invalid_json_and_content_type(self):
        for body in ("{", "[]", "null", '"text"', b"\xff"):
            with self.subTest(body=body):
                response = self.client.post(
                    self.url,
                    data=body,
                    content_type="application/json",
                    HTTP_X_CSRFTOKEN=self.token,
                )
                self.assertEqual(response.status_code, 400)
        self.assertEqual(
            self.client.post(
                self.url, data={}, HTTP_X_CSRFTOKEN=self.token
            ).status_code,
            400,
        )
