from typing import Protocol

from .import_challenge_package_input_data import ImportChallengePackageInputData


class ImportChallengePackageInputBoundary(Protocol):
    def execute(self, input_data: ImportChallengePackageInputData) -> None: ...
