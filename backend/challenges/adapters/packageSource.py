from pathlib import Path

from challenges.package import load_challenge_package
from challenges.useCases.ports import LoadedChallengePackage, PackageSource


class FileSystemPackageSource(PackageSource):
    def load(self, folder: Path) -> LoadedChallengePackage:
        return load_challenge_package(folder)
