from contextlib import contextmanager, nullcontext
from dataclasses import dataclass
from datetime import date
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.test import SimpleTestCase, override_settings

from challenges import package as package_module

from challenges.adapters.mediaStore import FileSystemMediaStore
from challenges.adapters.importChallengePackage.Presenter import (
    ImportChallengePackagePresenter,
)
from challenges.adapters.repositories import DjangoChallengeRepository
from challenges.domain.challenge import Challenge
from challenges.domain.challengePackage import (
    AudioValidationError,
    ChallengePackageError,
)
from challenges.adapters.importChallengePackage.Controller import (
    ImportChallengePackageController,
)
from challenges.useCases.importChallengePackage.InputData import (
    ImportChallengePackageInputData,
    PackageLocation,
)
from challenges.useCases.importChallengePackage.Interactor import (
    ImportChallengePackageInteractor,
)
from challenges.useCases.importChallengePackage.OutputData import (
    ImportChallengePackageFailureData,
    ImportChallengePackageFailureReason,
    ImportChallengePackageOutputData,
    ImportChallengePackageResultData,
)


def _loaded_package(slug="greeting", name="Greeting", challenge_date="2026-10-15"):
    folder = Path("/packages") / slug
    return SimpleNamespace(
        folder=folder,
        slug=slug,
        metadata={
            "name": name,
            "slug": slug,
            "challenge_date": challenge_date,
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

    def get_by_name(self, name):
        return next(
            (
                challenge
                for challenge in self.records.values()
                if challenge.name == name
            ),
            None,
        )

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
            [
                _loaded_package("greeting"),
                _loaded_package("farewell", "Farewell", "2026-10-16"),
            ]
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

    def test_skipped_existing_package_is_not_loaded_or_audio_validated(self):
        existing = Challenge(
            name="Greeting",
            slug="greeting",
            challenge_date=date(2026, 10, 15),
            difficulty=1,
            category="social",
            tone="friendly",
            required_action="greet warmly",
        )
        packages = InMemoryPackageSource([_loaded_package()])
        packages.error = ChallengePackageError("damaged package")
        audio = RecordingAudioValidator(
            error=AudioValidationError("ffprobe is unavailable")
        )
        media = RecordingMediaStore()
        interactor, presenter = self.build_interactor(
            challenges=InMemoryChallengeRepository([existing]),
            packages=packages,
            audio=audio,
            media=media,
        )

        interactor.execute(self.input_data(skip_existing=True))

        self.assertTrue(presenter.success.results[0].skipped)
        self.assertEqual(packages.loaded_folders, [])
        self.assertEqual(audio.calls, [])
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

    def test_existing_name_on_another_challenge_fails_before_saving(self):
        existing = Challenge(
            name="Greeting",
            slug="already-there",
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

        interactor.execute(self.input_data())

        self.assertEqual(
            presenter.failure.reason,
            ImportChallengePackageFailureReason.INVALID_PACKAGE,
        )
        self.assertIn("already used", presenter.failure.message)
        self.assertEqual(set(challenges.records), {"already-there"})
        self.assertEqual(media.installs, [])

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

    def test_duplicate_dates_fail_before_saving(self):
        packages = InMemoryPackageSource(
            [_loaded_package("greeting"), _loaded_package("farewell", "Farewell")]
        )
        challenges = InMemoryChallengeRepository()
        media = RecordingMediaStore()
        interactor, presenter = self.build_interactor(
            packages=packages,
            challenges=challenges,
            media=media,
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
        self.assertIn("duplicate challenge_date", presenter.failure.message)
        self.assertEqual(challenges.records, {})
        self.assertEqual(media.installs, [])

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


class DjangoChallengeRepositoryTests(SimpleTestCase):
    def test_save_translates_validation_error(self):
        challenge = Challenge(
            name="Greeting",
            slug="greeting",
            challenge_date=date(2026, 10, 15),
            difficulty=1,
            category="social",
            tone="friendly",
            required_action="greet warmly",
        )
        error = ValidationError({"name": ["already exists"]})

        with patch(
            "challenges.adapters.repositories.challenge_models.Challenge.objects.update_or_create",
            side_effect=error,
        ):
            with self.assertRaisesMessage(
                ChallengePackageError, "Could not save challenge"
            ):
                DjangoChallengeRepository().save(challenge)


class FileSystemMediaStoreTests(SimpleTestCase):
    def _prepared(self, slug, name, folder):
        challenge = Challenge(
            name=name,
            slug=slug,
            challenge_date=date(2026, 10, 15),
            difficulty=1,
            category="social",
            tone="friendly",
            required_action="greet warmly",
        )
        source = SimpleNamespace(
            folder=folder,
            slug=slug,
            files=frozenset({"audio/q1.mp3"}),
            turn_count=1,
        )
        return SimpleNamespace(challenge=challenge, source=source)

    def _write_package(self, folder):
        folder.mkdir()
        (folder / f"{folder.name}.json").write_text("{}", encoding="utf-8")
        (folder / "audio").mkdir()
        (folder / "audio" / "q1.mp3").write_bytes(b"audio")

    def test_staging_failure_becomes_package_error(self):
        with TemporaryDirectory() as root:
            item = self._prepared("greeting", "Greeting", Path(root) / "missing")

            with override_settings(MEDIA_ROOT=root):
                with self.assertRaisesMessage(
                    ChallengePackageError, "Could not stage challenge files"
                ):
                    FileSystemMediaStore().install([item], replace=False)

    def test_rollback_removes_installed_source_before_restoring_backup(self):
        with TemporaryDirectory() as root:
            root_path = Path(root)
            media_root = root_path / "media"
            source_root = root_path / "source"
            media_root.mkdir()
            source_root.mkdir()
            published_media = media_root / "challenges" / "first"
            published_source = source_root / "first"
            published_media.mkdir(parents=True)
            published_source.mkdir()
            (published_media / "old.txt").write_text("old media", encoding="utf-8")
            (published_source / "old.txt").write_text("old source", encoding="utf-8")

            first_folder = root_path / "first-package"
            second_folder = root_path / "second-package"
            self._write_package(first_folder)
            self._write_package(second_folder)
            first = self._prepared("first", "First", first_folder)
            second = self._prepared("second", "Second", second_folder)

            original_rename = Path.rename

            def fail_on_second_media(path, target):
                if (
                    path.name == "new"
                    and Path(target).parent == media_root / "challenges"
                    and Path(target).name == "second"
                ):
                    raise OSError("Simulated failure")
                return original_rename(path, target)

            with override_settings(MEDIA_ROOT=media_root):
                with patch.object(package_module, "CHALLENGES_DIR", source_root):
                    with patch.object(
                        Path, "rename", autospec=True, side_effect=fail_on_second_media
                    ):
                        with self.assertRaisesMessage(
                            ChallengePackageError, "Could not save challenge files"
                        ):
                            FileSystemMediaStore().install(
                                [first, second], replace=False
                            )

            self.assertEqual(
                (published_media / "old.txt").read_text(encoding="utf-8"), "old media"
            )
            self.assertEqual(
                (published_source / "old.txt").read_text(encoding="utf-8"),
                "old source",
            )
            self.assertFalse((media_root / "challenges" / "second").exists())
            self.assertFalse((source_root / "second").exists())


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
