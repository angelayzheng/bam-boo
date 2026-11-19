from dataclasses import dataclass

from challenges.use_cases.ports import ChallengeRepository, MediaStore
from play.use_cases.ports import AttemptRepository, ToneMatcher
from tone.use_cases.ports import ToneVectorRepository
from users.use_cases.ports import AuthGateway, GroupRepository, ProfileRepository


@dataclass(frozen=True, slots=True)
class ApplicationContainer:
    challenges: ChallengeRepository
    media: MediaStore
    attempts: AttemptRepository
    profiles: ProfileRepository
    tone_matcher: ToneMatcher
    tone_vectors: ToneVectorRepository
    auth: AuthGateway
    groups: GroupRepository


def build_container(
    *,
    challenges: ChallengeRepository,
    media: MediaStore,
    attempts: AttemptRepository,
    profiles: ProfileRepository,
    tone_matcher: ToneMatcher,
    tone_vectors: ToneVectorRepository,
    auth: AuthGateway,
    groups: GroupRepository,
) -> ApplicationContainer:
    """Collect infrastructure ports at the application composition boundary."""
    return ApplicationContainer(
        challenges=challenges,
        media=media,
        attempts=attempts,
        profiles=profiles,
        tone_matcher=tone_matcher,
        tone_vectors=tone_vectors,
        auth=auth,
        groups=groups,
    )
