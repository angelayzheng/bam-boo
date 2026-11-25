from dataclasses import dataclass

from users.useCases.profileData import ProfileData


@dataclass(frozen=True, slots=True)
class UpdateProfileOutputData:
    profile: ProfileData


@dataclass(frozen=True, slots=True)
class UpdateProfileFailureData:
    reason: str
    message: str
    collection_error: bool = False
