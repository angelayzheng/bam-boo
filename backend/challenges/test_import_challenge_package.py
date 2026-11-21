from contextlib import contextmanager, nullcontext
from dataclasses import dataclass
from datetime import date
from io import BytesIO
from pathlib import Path
from types import SimpleNamespace

from django.test import SimpleTestCase

from challenges.adapters.importChallengePackage.import_challenge_package_presenter import (
    ImportChallengePackagePresenter,
)
from challenges.domain.challenge import Challenge
from challenges.domain.challenge_package import (
    ChallengePackageError,
)
from challenges.adapters.importChallengePackage.import_challenge_package_controller import (
    ImportChallengePackageController,
)
from challenges.use_cases.importChallengePackage.import_challenge_package_input_data import (
    ImportChallengePackageInputData,
    PackageLocation,
)
from challenges.use_cases.importChallengePackage.import_challenge_package_interactor import (
    ImportChallengePackageInteractor,
)
from challenges.use_cases.importChallengePackage.import_challenge_package_output_data import (
    ImportChallengePackageFailureData,
    ImportChallengePackageFailureReason,
    ImportChallengePackageOutputData,
    ImportChallengePackageResultData,
)


def _loaded_package(slug="greeting", name="Greeting"):
    folder = Path("/packages") / slug
    return SimpleNamespace(
        folder=folder,
        slug=slug,
        metadata={
            "name": name,
            "slug": slug,
            "challenge_date": "2026-10-15",
            "difficulty": 1,
            "category": "social",
            "tone": "friendly",
            "required_action": "greet warmly",
        },
        conversation_tree={
            "type": "question",
            "node_key": "q1",
            "text_file": f"challenges/{slug}/transcripts/q1.txt",
            "audio_file": f"challenges/{slug}/audio/q1.mp3",
            "children": [],
        },
        files=frozenset({f"transcripts/q1.txt", f"audio/q1.mp3"}),
        turn_count=1,
    )


class InMemoryPackageSource:
    def __init__(self, packages):
        self.packages = {package.slug: package for package in packages}
        self.error = None
        self.loaded_folders = []

    def load(self, folder):
        self.loaded_folders.append(folder)
        if self.error is not None:
            raise self.error
        return self.packages[folder.name]


class FakeArchiveExtractor:
    def __init__(self, folder):
        self.folder = folder
        self.calls = []
        self.closed = False

    @contextmanager
    def extract(self, archive):
        self.calls.append(archive)
        yield self.folder
        self.closed = True


class RecordingAudioValidator:
    def __init__(self, error=None):
        self.error = error
        self.calls = []

    def validate(self, folder, relative_path):
        self.calls.append((folder, relative_path))
        if self.error is not None:
            raise self.error


class RecordingMediaStore:
    def __init__(self):
        self.installs = []

    def install(self, packages, *, replace):
        self.installs.append((tuple(packages), replace))


class InMemoryChallengeRepository:
    def __init__(self, challenges=()):
        self.records = {challenge.slug: challenge for challenge in challenges}

    def get_by_slug(self, slug):
        return self.records.get(slug)

    def save(self, challenge):
        self.records[challenge.slug] = challenge
        return challenge


class InMemoryUnitOfWork:
    def atomic(self):
        return nullcontext()


class RecordingOutputBoundary:
    def __init__(self):
        self.success = None
        self.failure = None

    def prepare_success_view(self, output_data):
        self.success = output_data

    def prepare_fail_view(self, failure):
        self.failure = failure


class ImportChallengePackageInteractorTests(SimpleTestCase):
    def build_interactor(
        self,
        *,
        packages=None,
        challenges=None,
        archives=None,
        audio=None,
        media=None,
        presenter=None,
    ):
        packages = packages or InMemoryPackageSource([_loaded_package()])
        challenges = challenges or InMemoryChallengeRepository()
        archives = archives or FakeArchiveExtractor(Path("/packages/greeting"))
        audio = audio or RecordingAudioValidator()
        media = media or RecordingMediaStore()
        presenter = presenter or RecordingOutputBoundary()
        interactor = ImportChallengePackageInteractor(
            challenges=challenges,
            packages=packages,
            archives=archives,
            audio=audio,
            media=media,
            unit_of_work=InMemoryUnitOfWork(),
            presenter=presenter,
        )
        return interactor, presenter

    def input_data(self, *, sources=None, **overrides):
        values = {
            "locations": sources
            or (PackageLocation(folder=Path("/packages/greeting")),),
            "replace": False,
            "skip_existing": False,
        }
        values.update(overrides)
        return ImportChallengePackageInputData(**values)

    def test_saves_all_packages_and_installs_media_once(self):
        packages = InMemoryPackageSource(
            [_loaded_package("greeting"), _loaded_package("farewell", "Farewell")]
        )
        challenges = InMemoryChallengeRepository()
        audio = RecordingAudioValidator()
        media = RecordingMediaStore()
        interactor, presenter = self.build_interactor(
            packages=packages,
            challenges=challenges,
            audio=audio,
            media=media,
        )
        locations = tuple(
            PackageLocation(folder=Path("/packages") / slug)
            for slug in ("greeting", "farewell")
        )

        interactor.execute(self.input_data(sources=locations))

        self.assertEqual(set(challenges.records), {"greeting", "farewell"})
        self.assertEqual(len(media.installs), 1)
        self.assertEqual(len(media.installs[0][0]), 2)
        self.assertEqual(len(audio.calls), 2)
        self.assertEqual(
            [result.slug for result in presenter.success.results],
            [
                "greeting",
                "farewell",
            ],
        )

    def test_existing_challenge_is_skipped_when_requested(self):
        existing = Challenge(
            name="Greeting",
            slug="greeting",
            challenge_date=date(2026, 10, 15),
            difficulty=1,
            category="social",
            tone="friendly",
            required_action="greet warmly",
        )
        challenges = InMemoryChallengeRepository([existing])
        media = RecordingMediaStore()
        interactor, presenter = self.build_interactor(
            challenges=challenges, media=media
        )

        interactor.execute(self.input_data(skip_existing=True))

        self.assertTrue(presenter.success.results[0].skipped)
        self.assertEqual(media.installs, [])

    def test_existing_challenge_fails_with_semantic_reason(self):
        existing = Challenge(
            name="Greeting",
            slug="greeting",
            challenge_date=date(2026, 10, 15),
            difficulty=1,
            category="social",
            tone="friendly",
            required_action="greet warmly",
        )
        media = RecordingMediaStore()
        interactor, presenter = self.build_interactor(
            challenges=InMemoryChallengeRepository([existing]), media=media
        )

        interactor.execute(self.input_data())

        self.assertEqual(
            presenter.failure.reason, ImportChallengePackageFailureReason.ALREADY_EXISTS
        )
        self.assertIn("already exists", presenter.failure.message)
        self.assertEqual(media.installs, [])
        self.assertFalse(hasattr(presenter.failure, "status_code"))

    def test_duplicate_names_fail_before_saving(self):
        packages = InMemoryPackageSource(
            [_loaded_package("greeting"), _loaded_package("farewell", "Greeting")]
        )
        challenges = InMemoryChallengeRepository()
        interactor, presenter = self.build_interactor(
            packages=packages,
            challenges=challenges,
        )
        locations = tuple(
            PackageLocation(folder=Path("/packages") / slug)
            for slug in ("greeting", "farewell")
        )

        interactor.execute(self.input_data(sources=locations))

        self.assertEqual(
            presenter.failure.reason,
            ImportChallengePackageFailureReason.INVALID_PACKAGE,
        )
        self.assertIn("duplicate name", presenter.failure.message)
        self.assertEqual(challenges.records, {})

    def test_invalid_package_becomes_a_semantic_failure(self):
        packages = InMemoryPackageSource([_loaded_package()])
        packages.error = ChallengePackageError("Invalid challenge package greeting")
        interactor, presenter = self.build_interactor(packages=packages)

        interactor.execute(self.input_data())

        self.assertEqual(
            presenter.failure.reason,
            ImportChallengePackageFailureReason.INVALID_PACKAGE,
        )
        self.assertEqual(
            presenter.failure.message, "Invalid challenge package greeting"
        )

    def test_archive_source_is_extracted(self):
        archive = BytesIO(b"zip")
        archives = FakeArchiveExtractor(Path("/packages/greeting"))
        packages = InMemoryPackageSource([_loaded_package()])
        interactor, presenter = self.build_interactor(
            packages=packages, archives=archives
        )

        interactor.execute(self.input_data(sources=(PackageLocation(archive=archive),)))

        self.assertEqual(archives.calls, [archive])
        self.assertTrue(archives.closed)
        self.assertEqual(packages.loaded_folders, [Path("/packages/greeting")])
        self.assertIsNotNone(presenter.success)


class ImportChallengePackageControllerTests(SimpleTestCase):
    def test_controller_creates_input_data_from_paths(self):
        recorded = []

        class Interactor:
            def execute(self, input_data):
                recorded.append(input_data)

        controller = ImportChallengePackageController(Interactor())
        folder = Path("/packages/greeting")

        controller.execute(sources=[folder], replace=True, skip_existing=True)

        self.assertEqual(recorded[0].locations, (PackageLocation(folder=folder),))
        self.assertTrue(recorded[0].replace)
        self.assertTrue(recorded[0].skip_existing)


class ImportChallengePackagePresenterTests(SimpleTestCase):
    def test_success_view_model_formats_messages(self):
        presenter = ImportChallengePackagePresenter()
        result = ImportChallengePackageResultData(
            slug="greeting",
            name="Greeting",
            challenge_date=date(2026, 10, 15),
            turn_count=3,
            replaced=False,
        )

        presenter.prepare_success_view(
            ImportChallengePackageOutputData(results=(result,))
        )

        self.assertTrue(presenter.view_model.success)
        self.assertEqual(
            presenter.view_model.message,
            "Imported Greeting (greeting) for 2026-10-15: 3 turns.",
        )

    def test_failure_view_model_has_no_results(self):
        presenter = ImportChallengePackagePresenter()

        presenter.prepare_fail_view(
            ImportChallengePackageFailureData(
                reason=ImportChallengePackageFailureReason.INVALID_PACKAGE,
                message="Upload a valid .zip archive.",
            )
        )

        self.assertFalse(presenter.view_model.success)
        self.assertEqual(presenter.view_model.message, "Upload a valid .zip archive.")
        self.assertEqual(presenter.view_model.results, ())
