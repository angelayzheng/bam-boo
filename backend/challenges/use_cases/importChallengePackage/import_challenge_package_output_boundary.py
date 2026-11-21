from typing import Protocol

from .import_challenge_package_output_data import (
    ImportChallengePackageFailureData,
    ImportChallengePackageOutputData,
)


class ImportChallengePackageOutputBoundary(Protocol):
    def prepare_success_view(
        self, output_data: ImportChallengePackageOutputData
    ) -> None: ...

    def prepare_fail_view(self, failure: ImportChallengePackageFailureData) -> None: ...
