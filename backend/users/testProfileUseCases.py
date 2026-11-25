from contextlib import contextmanager
from dataclasses import replace
from unittest import TestCase

from users.adapters.updateProfile.Controller import UpdateProfileController
from users.adapters.updateProfile.Presenter import UpdateProfilePresenter
from users.adapters.viewProfile.Controller import ViewProfileController
from users.adapters.viewProfile.Presenter import ViewProfilePresenter
from users.useCases.profileData import ProfileData
from users.useCases.updateProfile.InputData import UpdateProfileInputData
from users.useCases.updateProfile.Interactor import UpdateProfileInteractor
from users.useCases.viewProfile.InputData import ViewProfileInputData
from users.useCases.viewProfile.Interactor import ViewProfileInteractor


class RecordingOutput:
    def __init__(self):
        self.successes = []
        self.failures = []

    def prepare_success_view(self, output):
        self.successes.append(output)

    def prepare_fail_view(self, failure=None):
        self.failures.append(failure)


class FakeProfiles:
    def __init__(self):
        self.profile = ProfileData(
            user_id=7,
            username="ada",
            name="",
            email="ada@example.com",
            team="",
            avatar="fox",
            scores={"sample": 2},
            total_score=2,
            login_days=["2026-10-12", "2026-10-10"],
        )
        self.lookups = []
        self.updates = []
        self.in_transaction = False

    def get_by_user_id(self, user_id):
        self.lookups.append(("id", user_id))
        return self.profile if user_id == self.profile.user_id else None

    def get_by_username(self, username, *, for_update=False):
        if for_update:
            assert self.in_transaction
        self.lookups.append(("username", username, for_update))
        return self.profile if username == self.profile.username else None

    def update(self, user_id, changes):
        assert self.in_transaction
        self.updates.append((user_id, changes))
        fields = {
            key: changes[key]
            for key in ("name", "email", "avatar", "login_days")
            if key in changes
        }
        if "challenge_scores" in changes:
            fields.update(
                scores=changes["challenge_scores"], total_score=changes["total_score"]
            )
        self.profile = replace(self.profile, **fields)
        return self.profile


class ViewProfileTests(TestCase):
    def test_reads_by_id_or_username_and_reports_missing_profiles(self):
        profiles, output = FakeProfiles(), RecordingOutput()
        interactor = ViewProfileInteractor(profiles=profiles, presenter=output)
        interactor.execute(ViewProfileInputData(user_id=7))
        interactor.execute(ViewProfileInputData(username="ada"))
        interactor.execute(ViewProfileInputData(username="missing"))
        interactor.execute(ViewProfileInputData(user_id=99))
        self.assertEqual([item.by_username for item in output.successes], [False, True])
        self.assertEqual(output.failures, [None, None])
        self.assertEqual(
            profiles.lookups,
            [
                ("id", 7),
                ("username", "ada", False),
                ("username", "missing", False),
                ("id", 99),
            ],
        )

    def test_presenter_preserves_both_schemas_and_resets_status(self):
        presenter, profiles = ViewProfilePresenter(), FakeProfiles()
        controller = ViewProfileController(
            ViewProfileInteractor(profiles=profiles, presenter=presenter)
        )
        controller.execute(username="missing")
        self.assertEqual(presenter.status_code, 404)
        controller.execute(user_id=7)
        self.assertEqual(presenter.status_code, 200)
        self.assertEqual(
            presenter.response_body,
            {
                "user_id": 7,
                "username": "ada",
                "avatar": "fox",
                "total_score": 2,
                "completed_challenges": 1,
                "scores": {"sample": 2},
            },
        )
        controller.execute(username="ada")
        self.assertEqual(
            presenter.response_body,
            {
                "slug": "ada",
                "name": "ada",
                "email": "ada@example.com",
                "team": "",
                "challenge_scores": {"sample": 2},
                "total_score": 2.0,
                "login_days": ["2026-10-10", "2026-10-12"],
                "avatar": "fox",
            },
        )


class FakeTeams:
    def find_by_slug(self, slug):
        return {"alpha": [3], "ambiguous": [4, 5]}.get(slug, [])


class FakeEmailValidator:
    def is_valid(self, email):
        return email == "ada@example.com"


class FakeUnitOfWork:
    def __init__(self, profiles):
        self.profiles = profiles
        self.commits = 0

    @contextmanager
    def atomic(self):
        self.profiles.in_transaction = True
        try:
            yield
        except Exception:
            raise
        else:
            self.commits += 1
        finally:
            self.profiles.in_transaction = False


class UpdateProfileTests(TestCase):
    def setUp(self):
        self.profiles, self.output = FakeProfiles(), RecordingOutput()
        self.unit_of_work = FakeUnitOfWork(self.profiles)
        self.interactor = self.build_interactor(self.output)

    def build_interactor(self, presenter):
        return UpdateProfileInteractor(
            profiles=self.profiles,
            teams=FakeTeams(),
            email_validator=FakeEmailValidator(),
            unit_of_work=self.unit_of_work,
            presenter=presenter,
        )

    def execute(self, payload, *, username="ada", user_id=7, parsing_error=None):
        self.interactor.execute(
            UpdateProfileInputData(username, user_id, payload, parsing_error)
        )

    def test_updates_normalized_values_and_derives_scores_inside_a_transaction(self):
        self.execute(
            {
                "name": "  Ada Lovelace  ",
                "email": "ada@example.com",
                "team": "alpha",
                "avatar": "owl",
                "challenge_scores": {"sample": 1, "other": 3},
                "login_days": ["2026-10-12", "2026-10-10"],
            }
        )
        changes = self.profiles.updates[0][1]
        self.assertEqual(changes["name"], "Ada Lovelace")
        self.assertEqual(changes["group_id"], 3)
        self.assertEqual(changes["total_score"], 4)
        self.assertEqual(changes["login_days"], ["2026-10-10", "2026-10-12"])
        self.assertEqual(
            self.output.successes[0].profile.scores, {"sample": 1, "other": 3}
        )
        self.assertEqual(self.unit_of_work.commits, 1)
        self.assertEqual(self.profiles.lookups, [("username", "ada", True)])

    def test_authentication_and_ownership_precede_body_validation(self):
        for username, user_id, reason in (
            ("missing", None, "unauthenticated"),
            ("missing", 7, "not_found"),
            ("ada", 8, "forbidden"),
            ("ada", 7, "invalid"),
        ):
            with self.subTest(reason=reason):
                self.execute(
                    None,
                    username=username,
                    user_id=user_id,
                    parsing_error="Invalid body.",
                )
                self.assertEqual(self.output.failures[-1].reason, reason)
                self.assertFalse(hasattr(self.output.failures[-1], "status_code"))
        self.assertEqual(self.profiles.updates, [])

    def test_rejects_invalid_values_without_writing(self):
        cases = [
            {"unknown": True},
            {"slug": "other"},
            {"challenge_scores": None},
            {"challenge_scores": {"": 1}},
            {"challenge_scores": {"sample": True}},
            {"challenge_scores": {"sample": 4}},
            {"challenge_scores": {"sample": 1.5}},
            {"total_score": True},
            {"total_score": float("nan")},
            {"total_score": float("inf")},
            {"total_score": 100},
            {"name": " "},
            {"name": 1},
            {"name": "x" * 151},
            {"team": None},
            {"team": "missing"},
            {"team": "ambiguous"},
            {"login_days": {}},
            {"login_days": [1]},
            {"login_days": ["bad"]},
            {"login_days": ["2026-10-12", "2026-10-12"]},
            {"avatar": "unicorn"},
            {"avatar": []},
            {"email": 1},
            {"email": "x" * 255},
            {"email": "invalid"},
        ]
        for payload in cases:
            with self.subTest(payload=payload):
                self.execute(payload)
                self.assertEqual(self.output.failures[-1].reason, "invalid")
        self.assertEqual(len(self.output.failures), len(cases))
        self.assertEqual(self.profiles.updates, [])
        self.assertEqual(self.output.successes, [])

    def test_avatar_only_empty_patch_and_clearing_optional_values(self):
        for payload in (
            {"avatar": "owl"},
            {},
            {"team": "", "email": "", "challenge_scores": {}},
        ):
            self.execute(payload)
        self.assertEqual(self.output.failures, [])
        self.assertEqual(self.profiles.updates[-1][1]["group_id"], None)
        self.assertEqual(self.profiles.profile.total_score, 0)
        self.assertEqual(self.profiles.profile.email, "")

    def test_controller_parses_transport_and_presenter_resets_errors(self):
        presenter = UpdateProfilePresenter()
        controller = UpdateProfileController(self.build_interactor(presenter))
        for body, content_type, detail in (
            (b"{}", "text/plain", "Expected an application/json body."),
            (b"{", "application/json", "Expected a valid JSON object."),
            (b"\xff", "application/json", "Expected a valid JSON object."),
            (b"[]", "application/json", "Expected a JSON object."),
            (
                b'{"challenge_scores": {"sample": true}}',
                "application/json",
                "[\"Score for 'sample' must be a whole number.\"]",
            ),
            (
                b'{"login_days": ["bad"]}',
                "application/json",
                "[\"Invalid login day 'bad'; expected YYYY-MM-DD.\"]",
            ),
        ):
            controller.execute(
                username="ada", user_id=7, body=body, content_type=content_type
            )
            self.assertEqual(presenter.status_code, 400)
            self.assertEqual(presenter.response_body, {"detail": detail})
        controller.execute(
            username="ada",
            user_id=7,
            body=b'{"avatar": "owl"}',
            content_type="application/json",
        )
        self.assertEqual(presenter.status_code, 200)
        self.assertEqual(presenter.response_body["avatar"], "owl")
