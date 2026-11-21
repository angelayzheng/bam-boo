from dataclasses import dataclass

from challenges.use_cases.importChallengePackage.import_challenge_package_output_boundary import (
    ImportChallengePackageOutputBoundary,
)
from challenges.use_cases.importChallengePackage.import_challenge_package_output_data import (
    ImportChallengePackageFailureData,
    ImportChallengePackageOutputData,
    ImportChallengePackageResultData,
)


@dataclass(frozen=True, slots=True)
class ImportChallengePackageViewModel:
    success: bool
    message: str
    results: tuple[ImportChallengePackageResultData, ...] = ()


class ImportChallengePackagePresenter(ImportChallengePackageOutputBoundary):
    def __init__(self):
        self.view_model = ImportChallengePackageViewModel(success=False, message="")

    def prepare_success_view(
        self, output_data: ImportChallengePackageOutputData
    ) -> None:
        messages = []
        for result in output_data.results:
            if result.skipped:
                messages.append("Challenge already exists; use --replace to update it.")
                continue
            action = "Replaced" if result.replaced else "Imported"
            messages.append(
                f"{action} {result.name} ({result.slug}) for "
                f"{result.challenge_date}: {result.turn_count} turns."
            )
        self.view_model = ImportChallengePackageViewModel(
            success=True,
            message=" ".join(messages),
            results=output_data.results,
        )

    def prepare_fail_view(self, failure: ImportChallengePackageFailureData) -> None:
        self.view_model = ImportChallengePackageViewModel(
            success=False, message=failure.message
        )
