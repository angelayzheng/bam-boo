from datetime import date
from unittest import TestCase

from users.domain.profile import Profile
from users.domain.profileChanges import ProfileChanges


class ProfileDomainTests(TestCase):
    def test_scores_keep_the_best_attempt_and_derive_the_total(self):
        profile = Profile(user_id=1, username="ada")
        profile.add_score("first", 3)
        profile.add_score("first", 1)
        profile.add_score("second", 2)
        self.assertEqual(profile.scores, {"first": 3, "second": 2})
        self.assertEqual(profile.total_score, 5)

    def test_rejected_scores_do_not_mutate_progress(self):
        profile = Profile(user_id=1, username="ada", scores={"first": 2})
        for score in (-1, 4, True, 1.5, "3", None):
            with self.subTest(score=score):
                with self.assertRaises(ValueError):
                    profile.add_score("first", score)
                self.assertEqual(profile.scores, {"first": 2})

    def test_login_days_are_sorted_unique_and_have_a_consecutive_streak(self):
        profile = Profile(user_id=1, username="ada")
        for day in (date(2026, 10, 14), date(2026, 10, 12), date(2026, 10, 14)):
            profile.record_login(day)
        self.assertEqual(profile.login_days, [date(2026, 10, 12), date(2026, 10, 14)])
        profile.record_login(date(2026, 10, 13))
        self.assertEqual(profile.streak(date(2026, 10, 15)), 3)
        self.assertEqual(profile.streak(date(2026, 10, 16)), 0)
        with self.assertRaises(ValueError):
            profile.record_login("2026-10-15")

    def test_profile_changes_validate_account_details_and_distinguish_omitted_fields(
        self,
    ):
        self.assertEqual(ProfileChanges(name=" Ada ").name, "Ada")
        self.assertIsNone(ProfileChanges().email)
        self.assertEqual(ProfileChanges(email="", team="").email, "")
        for fields in (
            {"name": " "},
            {"name": "x" * 151},
            {"name": 1},
            {"team": []},
            {"avatar": "unicorn"},
            {"avatar": []},
            {"email": "x" * 255},
            {"email": 1},
        ):
            with self.subTest(fields=fields), self.assertRaises(ValueError):
                ProfileChanges(**fields)
