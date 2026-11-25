import json
from array import array
from uuid import uuid4

from django.contrib.auth.models import User
from django.test import Client, TestCase

from play.models import ChallengeRun
from challenges.models import Challenge
from challenges.testSupport import make_challenge
from tone.models import ToneVector

from .models import ChallengeAttempt, UserProfile


class ChallengeRunApiTests(TestCase):
    def setUp(self):
        self.client = Client(enforce_csrf_checks=True)
        self.user = User.objects.create_user(
            username="ada", password="Score!Maple7River"
        )
        self.other = User.objects.create_user(
            username="grace", password="Other!Maple7River"
        )
        self.challenge = make_challenge(tone="calm", required_action="reset password")
        ToneVector.objects.create(word="calm", vector=array("f", [1.0, 0.0]).tobytes())
        self.refresh_csrf()

    def refresh_csrf(self):
        self.token = self.client.get("/api/users/auth/csrf/").json()["csrfToken"]

    def post_json(self, path, payload):
        return self.client.post(
            path,
            data=json.dumps(payload),
            content_type="application/json",
            HTTP_X_CSRFTOKEN=self.token,
        )

    def start(self):
        response = self.post_json(
            f"/api/challenges/{self.challenge.slug}/attempts/", {}
        )
        self.assertEqual(response.status_code, 201, response.content)
        return response.json()

    def test_challenge_details_and_started_run_do_not_expose_answers_or_future_nodes(
        self,
    ):
        detail = self.client.get(f"/api/challenges/{self.challenge.slug}/")
        self.assertEqual(detail.status_code, 200)
        self.assertNotIn("tone", detail.json())
        self.assertNotIn("required_action", detail.json())
        self.assertNotIn("conversation_tree", detail.json())

        run = self.start()
        self.assertEqual(run["stage"], "tone")
        self.assertEqual(run["opening"]["id"], "q1")
        self.assertEqual(run["choices"], [])
        self.assertNotIn("tone", run)
        self.assertNotIn("required_action", run)
        self.assertNotIn("conversation_tree", run)

    def test_run_requires_ordered_transitions_and_returns_only_current_choices(self):
        run = self.start()
        run_url = f"/api/attempts/{run['attempt_id']}"
        self.assertEqual(
            self.post_json(f"{run_url}/choices/", {"choice_id": "0"}).status_code,
            409,
        )

        tone = self.post_json(f"{run_url}/tone/", {"answer": "calm"})
        self.assertEqual(tone.status_code, 200, tone.content)
        tone_payload = tone.json()
        self.assertEqual(tone_payload["stage"], "conversation")
        self.assertTrue(tone_payload["tone_correct"])
        self.assertEqual(len(tone_payload["choices"]), 1)
        self.assertEqual(tone_payload["choices"][0]["id"], "r1")
        self.assertEqual(tone_payload["choices"][0]["choice_id"], "0")

        invalid_choice = self.post_json(f"{run_url}/choices/", {"choice_id": "99"})
        self.assertEqual(invalid_choice.status_code, 400)
        chosen = self.post_json(f"{run_url}/choices/", {"choice_id": "0"})
        self.assertEqual(chosen.status_code, 200, chosen.content)
        self.assertEqual(chosen.json()["stage"], "conversation")
        self.assertEqual(
            [turn["id"] for turn in chosen.json()["conversation"]],
            ["q1", "r1", "q2"],
        )
        self.assertEqual(chosen.json()["choices"], [])

        continued = self.post_json(f"{run_url}/continue/", {})
        self.assertEqual(continued.status_code, 200, continued.content)
        self.assertEqual(continued.json()["stage"], "action")
        self.assertEqual(self.post_json(f"{run_url}/continue/", {}).status_code, 409)

        completed = self.post_json(f"{run_url}/action/", {"answer": "reset password"})
        self.assertEqual(completed.status_code, 200, completed.content)
        self.assertEqual(completed.json()["stage"], "completed")
        self.assertTrue(completed.json()["action_correct"])
        self.assertEqual(completed.json()["score"], 3)
        self.assertIsNotNone(completed.json()["completed_at"])
        self.assertIsNone(completed.json()["user_id"])
        self.assertFalse(completed.json()["saved"])
        self.assertEqual(
            ChallengeRun.objects.get(pk=run["attempt_id"]).stage, "completed"
        )

    def test_attempt_owner_is_enforced_and_run_can_be_resumed(self):
        self.client.force_login(self.user)
        self.refresh_csrf()
        run = self.start()
        run_url = f"/api/attempts/{run['attempt_id']}/"
        self.assertEqual(self.client.get(run_url).status_code, 200)

        self.client.force_login(self.other)
        self.refresh_csrf()
        self.assertEqual(self.client.get(run_url).status_code, 403)
        self.assertEqual(
            self.post_json(f"{run_url}tone/", {"answer": "calm"}).status_code, 403
        )

    def test_completed_run_is_the_only_source_for_profile_scores(self):
        run = self.start()
        run_url = f"/api/attempts/{run['attempt_id']}"
        self.post_json(f"{run_url}/tone/", {"answer": "calm"})
        self.post_json(f"{run_url}/choices/", {"choice_id": "0"})
        self.post_json(f"{run_url}/continue/", {})
        self.post_json(f"{run_url}/action/", {"answer": "reset password"})

        self.client.force_login(self.user)
        self.refresh_csrf()
        score_url = f"/api/users/me/scores/{self.challenge.slug}/"
        response = self.post_json(score_url, {"attempt_id": run["attempt_id"]})
        self.assertEqual(response.status_code, 201, response.content)
        self.assertEqual(response.json()["scores"], {self.challenge.slug: 3})
        self.assertEqual(ChallengeAttempt.objects.count(), 1)
        self.assertEqual(
            ChallengeRun.objects.get(pk=run["attempt_id"]).user_id, self.user.pk
        )

        repeated = self.post_json(score_url, {"attempt_id": run["attempt_id"]})
        self.assertEqual(repeated.status_code, 200)
        self.assertEqual(ChallengeAttempt.objects.count(), 1)
        self.assertEqual(UserProfile.objects.get(user=self.user).total_score, 3)

    def test_authenticated_completion_is_saved_to_the_users_profile(self):
        self.client.force_login(self.user)
        self.refresh_csrf()
        run = self.start()
        run_url = f"/api/attempts/{run['attempt_id']}"
        self.post_json(f"{run_url}/tone/", {"answer": "calm"})
        self.post_json(f"{run_url}/choices/", {"choice_id": "0"})
        self.post_json(f"{run_url}/continue/", {})

        completed = self.post_json(f"{run_url}/action/", {"answer": "reset password"})

        self.assertEqual(completed.status_code, 200, completed.content)
        profile = UserProfile.objects.get(user=self.user)
        self.assertEqual(
            profile.scores, {self.challenge.slug: completed.json()["score"]}
        )
        self.assertEqual(profile.total_score, completed.json()["score"])
        self.assertEqual(ChallengeAttempt.objects.count(), 1)
        self.assertEqual(completed.json()["user_id"], self.user.pk)
        self.assertTrue(completed.json()["saved"])

        score_url = f"/api/users/me/scores/{self.challenge.slug}/"
        redundant_claim = self.post_json(score_url, {"attempt_id": run["attempt_id"]})
        self.assertEqual(redundant_claim.status_code, 200)
        self.assertEqual(ChallengeAttempt.objects.count(), 1)

    def test_score_claim_requires_a_completion_timestamp(self):
        self.client.force_login(self.user)
        self.refresh_csrf()
        run = ChallengeRun.objects.create(
            challenge=self.challenge,
            user=None,
            stage="completed",
            current_node="q1",
            score=3,
            completed_at=None,
        )

        response = self.post_json(
            f"/api/users/me/scores/{self.challenge.slug}/",
            {"attempt_id": str(run.pk)},
        )

        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json(), {"detail": "The attempt is not complete."})
        self.assertEqual(ChallengeAttempt.objects.count(), 0)

    def test_score_endpoint_rejects_client_calculated_results(self):
        self.client.force_login(self.user)
        self.refresh_csrf()
        response = self.post_json(
            f"/api/users/me/scores/{self.challenge.slug}/",
            {
                "attempt_id": "00000000-0000-0000-0000-000000000001",
                "tone_correct": True,
                "tone_time": 0,
                "action_correct": True,
                "score": 999,
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(ChallengeAttempt.objects.count(), 0)
        self.assertEqual(UserProfile.objects.get(user=self.user).scores, {})

    def test_tone_submission_is_a_post_belonging_to_a_run(self):
        run = self.start()
        run_url = f"/api/attempts/{run['attempt_id']}/tone/"
        self.assertEqual(self.client.get(run_url).status_code, 405)
        self.assertEqual(
            self.post_json(run_url, {"answer": "unlisted"}).status_code, 422
        )
        self.assertEqual(Challenge.objects.count(), 1)

    def test_tone_submission_rejects_answers_longer_than_200_characters(self):
        run = self.start()
        run_url = f"/api/attempts/{run['attempt_id']}/tone/"

        response = self.post_json(run_url, {"answer": "a" * 201})

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json(),
            {"detail": "answer must be at most 200 characters."},
        )
        self.assertEqual(
            ChallengeRun.objects.get(pk=run["attempt_id"]).stage,
            "tone",
        )

    def test_missing_attempt_is_not_reported_as_an_unknown_tone(self):
        missing_url = f"/api/attempts/{uuid4()}/tone/"
        missing = self.post_json(missing_url, {"answer": "calm"})
        self.assertEqual(missing.status_code, 404)

        run = self.start()
        unknown = self.post_json(
            f"/api/attempts/{run['attempt_id']}/tone/", {"answer": "unlisted"}
        )
        self.assertEqual(unknown.status_code, 422)
        self.assertNotEqual(missing.status_code, unknown.status_code)
