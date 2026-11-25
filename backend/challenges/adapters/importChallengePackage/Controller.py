from collections.abc import Sequence
from pathlib import Path
from typing import BinaryIO

from challenges.useCases.importChallengePackage.InputBoundary import (
    ImportChallengePackageInputBoundary,
)
from challenges.useCases.importChallengePackage.InputData import (
    ImportChallengePackageInputData,
    PackageLocation,
)


class ImportChallengePackageController:
    def __init__(self, interactor: ImportChallengePackageInputBoundary):
        self._interactor = interactor

    def execute(
        self,
        *,
        sources: Sequence[Path | BinaryIO],
        replace: bool = False,
        skip_existing: bool = False,
    ) -> None:
        locations = tuple(PackageLocation.from_source(source) for source in sources)
        self._interactor.execute(
            ImportChallengePackageInputData(
                locations=locations,
                replace=replace,
                skip_existing=skip_existing,
            )
        )
