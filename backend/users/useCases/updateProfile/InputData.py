from dataclasses import dataclass

from users.domain.profileChanges import ProfileChanges


@dataclass(frozen=True, slots=True)
class UpdateProfileInputData:
    username: str
    user_id: int | None
    changes: ProfileChanges
