from datetime import date, datetime, timezone

from django.test import SimpleTestCase

from challenges.domain.challenge import Challenge
from challenges.domain.conversation_node import ConversationNode
from play.domain.answer_matching import AnswerMatching
from play.domain.attempt import Attempt
from play.domain.star_rules import StarRules
from users.domain.profile import Profile


class DomainEntityTests(SimpleTestCase):
    def test_challenge_builds_and_validates_alternating_conversation(self):
        challenge = Challenge(
            name="Password reset",
            slug="password-reset",
            challenge_date=date(2026, 11, 19),
            difficulty=2,
            category="account",
            tone="frustrated",
            required_action="reset password",
            conversation_tree={
                "type": "question",
                "text_file": "transcripts/customer.txt",
                "audio_file": "audio/customer.mp3",
                "children": [
                    {
                        "type": "response",
                        "text_file": "transcripts/agent.txt",
                        "audio_file": "audio/agent.mp3",
                    }
                ],
            },
        )

        self.assertIsInstance(challenge.conversation_tree, ConversationNode)
        with self.assertRaisesRegex(ValueError, "Expected a 'question' node"):
            ConversationNode.from_dict(
                {
                    "type": "response",
                    "text_file": "transcripts/customer.txt",
                    "audio_file": "audio/customer.mp3",
                }
            )
        with self.assertRaisesRegex(ValueError, "Invalid media filename"):
            ConversationNode.from_dict(
                {
                    "type": "question",
                    "text_file": "../customer.txt",
                    "audio_file": "audio/customer.mp3",
                }
            )

    def test_profile_keeps_best_score_and_calculates_streak(self):
        profile = Profile(user_id=3, username="ada")
        profile.add_score("day-one", 3)
        profile.add_score("day-one", 1)
        profile.record_login(date(2026, 11, 17))
        profile.record_login(date(2026, 11, 18))

        self.assertEqual(profile.scores, {"day-one": 3})
        self.assertEqual(profile.total_score, 3)
        self.assertEqual(profile.streak(date(2026, 11, 19)), 2)

    def test_attempt_requires_aware_completion_time_and_matches_retry(self):
        completed_at = datetime(2026, 11, 19, 12, tzinfo=timezone.utc)
        attempt = Attempt("submission", 7, "day-one", 2, completed_at)

        self.assertTrue(attempt.matches_completion(7, "day-one", 2, completed_at))
        with self.assertRaisesRegex(ValueError, "timezone-aware"):
            Attempt("submission", 7, "day-one", 2, datetime(2026, 11, 19, 12))

    def test_star_rules_apply_each_of_three_independent_stars(self):
        rules = StarRules()

        self.assertEqual(rules.score(True, 10, False), 2)
        self.assertEqual(rules.score(False, 10.01, True), 1)

    def test_answer_matching_uses_a_similarity_threshold_and_whole_words(self):
        self.assertTrue(AnswerMatching.tone_is_correct(0.65))
        self.assertFalse(AnswerMatching.tone_is_correct(0.649))
        self.assertTrue(
            AnswerMatching.action_is_correct("reset password", "Please reset password.")
        )
        self.assertFalse(
            AnswerMatching.action_is_correct("reset password", "reset passwords")
        )
