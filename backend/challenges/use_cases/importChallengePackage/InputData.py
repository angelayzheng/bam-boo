from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO


@dataclass(frozen=True, slots=True)
class PackageLocation:
    folder: Path | None = None
    archive: BinaryIO | None = None

    @classmethod
    def from_source(cls, source: str | Path | BinaryIO) -> "PackageLocation":
        if isinstance(source, (str, Path)):
            return cls(folder=Path(source))
        return cls(archive=source)

    def __post_init__(self):
        if (self.folder is None) == (self.archive is None):
            raise ValueError("A package source must be a folder or an archive.")


@dataclass(frozen=True, slots=True)
class ImportChallengePackageInputData:
    locations: tuple[PackageLocation, ...]
    replace: bool = False
    skip_existing: bool = False

    def __post_init__(self):
        if not self.locations:
            raise ValueError("At least one challenge package is required.")
