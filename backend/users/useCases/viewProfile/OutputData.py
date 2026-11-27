from dataclasses import dataclass

from users.useCases.profileData import ProfileData


@dataclass(frozen=True, slots=True)
class ViewProfileOutputData:
    profile: ProfileData
    by_username: bool
