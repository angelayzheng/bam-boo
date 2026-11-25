"""Tests for the browse-challenges interactor, using fakes instead of the database."""

from datetime import date
from unittest import TestCase

from challenges.use_cases.browseChallenges.DataAccessInterface import (
    BrowseChallengesDataAccessInterface,
    ChallengeRecord,
)
from challenges.use_cases.browseChallenges.InputData import (
    BrowseChallengesInputData,
)
from challenges.use_cases.browseChallenges.Interactor import (
    BrowseChallengesInteractor,
)
from challenges.use_cases.browseChallenges.OutputBoundary import (
    BrowseChallengesOutputBoundary,
)

from django.contrib.auth.models import User
from django.test import TestCase as DjangoTestCase

from challenges.testSupport import make_challenge

TODAY = date(2026, 10, 15)


def record(record_id, day, slug):
    return ChallengeRecord(
        id=record_id,
        name=slug.title(),
        challenge_date=day,
        slug=slug,
        difficulty=1,
        category="work",
    )


class FakeDataAccess(BrowseChallengesDataAccessInterface):
    def __init__(self, records=(), scores=None):
        self.records = list(records)
        self.scores = scores or {}
        self.month_calls = 0
        self.score_calls = 0

    def challenges_in_month(self, year, month):
        self.month_calls += 1
        return self.records

    def best_scores(self, user_id, challenge_ids):
        self.score_calls += 1
        return self.scores


class FakePresenter(BrowseChallengesOutputBoundary):
    def __init__(self):
        self.output = None
        self.error = None

    def prepare_success_view(self, output):
        self.output = output

    def prepare_fail_view(self, message):
        self.error = message


class BrowseChallengesInteractorTests(TestCase):
    def run_interactor(self, records=(), scores=None, user_id=1, year=2026, month=10):
        data_access = FakeDataAccess(records, scores)
        presenter = FakePresenter()
        BrowseChallengesInteractor(data_access, presenter, today=lambda: TODAY).execute(
            BrowseChallengesInputData(year=year, month=month, user_id=user_id)
        )
        return data_access, presenter

    def days_by_date(self, presenter):
        return {d.date: d for d in presenter.output.days}

    def test_returns_one_entry_per_day_of_the_month(self):
        _, presenter = self.run_interactor()
        self.assertEqual(len(presenter.output.days), 31)

    def test_day_without_a_challenge_is_none_with_empty_fields(self):
        _, presenter = self.run_interactor()
        day = self.days_by_date(presenter)[date(2026, 10, 1)]
        self.assertEqual(day.status, "none")
        self.assertIsNone(day.slug)
        self.assertIsNone(day.stars)

    def test_scored_challenge_is_completed_with_stars(self):
        records = [record(1, date(2026, 10, 5), "greeting")]
        _, presenter = self.run_interactor(records, scores={1: 3})
        day = self.days_by_date(presenter)[date(2026, 10, 5)]
        self.assertEqual(
            (day.status, day.stars, day.slug), ("completed", 3, "greeting")
        )

    def test_a_score_of_zero_still_counts_as_completed(self):
        records = [record(1, date(2026, 10, 5), "greeting")]
        _, presenter = self.run_interactor(records, scores={1: 0})
        day = self.days_by_date(presenter)[date(2026, 10, 5)]
        self.assertEqual((day.status, day.stars), ("completed", 0))

    def test_unscored_challenge_today_is_available(self):
        records = [record(1, TODAY, "greeting")]
        _, presenter = self.run_interactor(records)
        self.assertEqual(self.days_by_date(presenter)[TODAY].status, "available")

    def test_unscored_challenge_in_the_future_is_upcoming(self):
        records = [record(1, date(2026, 10, 20), "greeting")]
        _, presenter = self.run_interactor(records)
        self.assertEqual(
            self.days_by_date(presenter)[date(2026, 10, 20)].status, "upcoming"
        )

    def test_unscored_challenge_in_the_past_is_missed(self):
        records = [record(1, date(2026, 10, 10), "greeting")]
        _, presenter = self.run_interactor(records)
        day = self.days_by_date(presenter)[date(2026, 10, 10)]
        self.assertEqual((day.status, day.stars), ("missed", None))

    def test_guest_does_not_look_up_scores(self):
        records = [record(1, date(2026, 10, 10), "greeting")]
        data_access, presenter = self.run_interactor(records, user_id=None)
        self.assertEqual(data_access.score_calls, 0)
        self.assertEqual(
            self.days_by_date(presenter)[date(2026, 10, 10)].status, "missed"
        )

    def test_invalid_month_fails_without_touching_data_access(self):
        data_access, presenter = self.run_interactor(month=13)
        self.assertEqual(presenter.error, "Month must be between 1 and 12.")
        self.assertIsNone(presenter.output)
        self.assertEqual(data_access.month_calls, 0)


class CalendarEndpointTests(DjangoTestCase):
    url = "/api/calendar/"

    def setUp(self):
        self.challenge = make_challenge(
            name="Greeting", slug="greeting", challenge_date="2026-10-05"
        )

    def day(self, response, iso_date):
        return next(d for d in response.json()["days"] if d["date"] == iso_date)

    def test_rejects_missing_or_non_numeric_parameters(self):
        for query in [
            "",
            "?year=2026",
            "?month=10",
            "?year=abc&month=10",
            "?year=2026&month=oct",
        ]:
            with self.subTest(query=query):
                response = self.client.get(f"{self.url}{query}")
                self.assertEqual(response.status_code, 400)
                self.assertIn("detail", response.json())

    def test_rejects_out_of_range_year_and_month(self):
        for query in [
            "year=0&month=10",
            "year=10000&month=10",
            "year=2026&month=13",
            "year=2026&month=0",
        ]:
            with self.subTest(query=query):
                response = self.client.get(f"{self.url}?{query}")
                self.assertEqual(response.status_code, 400)
                self.assertIn("detail", response.json())

    def test_guest_gets_the_month_without_scores(self):
        response = self.client.get(f"{self.url}?year=2026&month=10")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(
            (body["year"], body["month"], len(body["days"])), (2026, 10, 31)
        )
        day = self.day(response, "2026-10-05")
        self.assertEqual(
            (day["status"], day["stars"], day["slug"]), ("missed", None, "greeting")
        )
        self.assertEqual(self.day(response, "2026-10-01")["status"], "none")

    def test_authenticated_user_sees_their_scores(self):
        user = User.objects.create_user(username="agent", password="pw")
        user.profile.add_score("greeting", 2)
        user.profile.save()
        self.client.force_login(user)

        response = self.client.get(f"{self.url}?year=2026&month=10")
        day = self.day(response, "2026-10-05")
        self.assertEqual((day["status"], day["stars"]), ("completed", 2))

    def test_only_get_is_allowed(self):
        response = self.client.post(f"{self.url}?year=2026&month=10")
        self.assertEqual(response.status_code, 405)
