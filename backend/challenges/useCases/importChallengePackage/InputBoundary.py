from typing import Protocol

from .InputData import ImportChallengePackageInputData


class ImportChallengePackageInputBoundary(Protocol):
    def execute(self, input_data: ImportChallengePackageInputData) -> None: ...
