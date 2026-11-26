from contextlib import contextmanager
from dataclasses import replace
from unittest import TestCase
from unittest.mock import Mock

from users.domain.profileChanges import ProfileChanges

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

    def update(self, user_id, changes, *, group_id):
        assert self.in_transaction
        self.updates.append((user_id, changes, group_id))
        fields = {
            key: getattr(changes, key)
            for key in ("name", "email", "avatar", "team")
            if getattr(changes, key) is not None
        }
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

    def execute(self, changes=None, *, username="ada", user_id=7):
        self.interactor.execute(
            UpdateProfileInputData(
                username=username,
                user_id=user_id,
                changes=ProfileChanges() if changes is None else changes,
            )
        )

    def test_updates_typed_account_details_without_replacing_progress(self):
        self.execute(
            ProfileChanges(
                name="  Ada Lovelace  ",
                email="ada@example.com",
                team="alpha",
                avatar="owl",
            )
        )
        user_id, changes, group_id = self.profiles.updates[0]
        self.assertEqual(user_id, 7)
        self.assertEqual(changes.name, "Ada Lovelace")
        self.assertEqual(group_id, 3)
        self.assertEqual(self.output.successes[0].profile.scores, {"sample": 2})
        self.assertEqual(
            self.output.successes[0].profile.login_days, ["2026-10-12", "2026-10-10"]
        )
        self.assertEqual(self.unit_of_work.commits, 1)
        self.assertEqual(self.profiles.lookups, [("username", "ada", True)])

    def test_authentication_and_ownership_prevent_persistence(self):
        for username, user_id, reason in (
            ("missing", None, "unauthenticated"),
            ("missing", 7, "not_found"),
            ("ada", 8, "forbidden"),
        ):
            with self.subTest(reason=reason):
                self.execute(username=username, user_id=user_id)
                self.assertEqual(self.output.failures[-1].reason, reason)
                self.assertFalse(hasattr(self.output.failures[-1], "status_code"))
        self.assertEqual(self.profiles.updates, [])

    def test_rejects_invalid_email_and_missing_or_ambiguous_teams(self):
        for changes in (
            ProfileChanges(email="invalid"),
            ProfileChanges(team="missing"),
            ProfileChanges(team="ambiguous"),
        ):
            self.execute(changes)
            self.assertEqual(self.output.failures[-1].reason, "invalid")
        self.assertEqual(self.profiles.updates, [])
        self.assertEqual(self.output.successes, [])

    def test_avatar_only_empty_patch_and_clearing_optional_values(self):
        for changes in (
            ProfileChanges(avatar="owl"),
            ProfileChanges(),
            ProfileChanges(team="", email=""),
        ):
            self.execute(changes)
        self.assertEqual(self.output.failures, [])
        self.assertIsNone(self.profiles.updates[-1][2])
        self.assertEqual(self.profiles.profile.total_score, 2)
        self.assertEqual(self.profiles.profile.email, "")

    def test_controller_rejects_invalid_transport_without_calling_interactor(self):
        presenter = UpdateProfilePresenter()
        interactor = Mock()
        controller = UpdateProfileController(interactor, presenter)
        for body, content_type in (
            (b"{}", "text/plain"),
            (b"{", "application/json"),
            (b"\xff", "application/json"),
            (b"[]", "application/json"),
            (b'{"challenge_scores": {"sample": 3}}', "application/json"),
            (b'{"total_score": 2}', "application/json"),
            (b'{"login_days": []}', "application/json"),
            (b'{"email": null}', "application/json"),
            (b'{"avatar": "unicorn"}', "application/json"),
            (b'{"slug": "other"}', "application/json"),
            (b'{"name": " "}', "application/json"),
        ):
            with self.subTest(body=body):
                controller.execute(
                    username="ada", user_id=7, body=body, content_type=content_type
                )
                self.assertEqual(presenter.status_code, 400)
                interactor.execute.assert_not_called()
        controller.execute(
            username="ada",
            user_id=7,
            body=b'{"name": " Ada ", "email": ""}',
            content_type="application/json",
        )
        interactor.execute.assert_called_once_with(
            UpdateProfileInputData("ada", 7, ProfileChanges(name="Ada", email=""))
        )

    def test_controller_and_presenter_clear_an_old_error_on_success(self):
        presenter = UpdateProfilePresenter()
        controller = UpdateProfileController(
            self.build_interactor(presenter), presenter
        )
        controller.execute(
            username="ada", user_id=7, body=b"{", content_type="application/json"
        )
        self.assertEqual(presenter.status_code, 400)
        controller.execute(
            username="ada",
            user_id=7,
            body=b'{"avatar": "owl"}',
            content_type="application/json",
        )
        self.assertEqual(presenter.status_code, 200)
        self.assertEqual(presenter.response_body["avatar"], "owl")
        self.assertNotIn("email", presenter.response_body)
