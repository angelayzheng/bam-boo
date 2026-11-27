from collections.abc import Sequence
from datetime import date

from django.contrib.auth.models import Group
from django.utils.text import slugify

from users.domain.profile import Profile
from users.domain.profileChanges import ProfileChanges
from users.models import UserProfile
from users.useCases.ports import (
    ProfileDetailsRepository,
    ProfileRepository,
    TeamRepository,
)
from users.useCases.profileData import ProfileData


def _to_domain(row: UserProfile) -> Profile:
    return Profile(
        user_id=row.user_id,
        username=row.user.username,
        record_id=row.pk,
        avatar=row.avatar,
        team=slugify(row.group.name) if row.group_id else None,
        scores=dict(row.scores),
        login_days=[date.fromisoformat(value) for value in row.login_days],
    )


class DjangoProfileRepository(ProfileRepository):
    def get_by_user_id(
        self, user_id: int, *, for_update: bool = False
    ) -> Profile | None:
        query = UserProfile.objects.select_related("user", "group")
        if for_update:
            query = query.select_for_update()
        row = query.filter(user_id=user_id).first()
        return None if row is None else _to_domain(row)

    def get_by_username(self, username: str) -> Profile | None:
        row = (
            UserProfile.objects.select_related("user", "group")
            .filter(user__username=username)
            .first()
        )
        return None if row is None else _to_domain(row)

    def list_top(self, limit: int) -> Sequence[Profile]:
        rows = UserProfile.objects.select_related("user", "group").order_by(
            "-total_score"
        )[:limit]
        return [_to_domain(row) for row in rows]

    def save(self, profile: Profile) -> Profile:
        row = UserProfile.objects.select_related("user", "group").get(
            user_id=profile.user_id
        )
        row.avatar = profile.avatar
        row.scores = dict(profile.scores)
        row.total_score = profile.total_score
        row.login_days = [day.isoformat() for day in profile.login_days]
        row.save(
            update_fields=[
                "avatar",
                "scores",
                "total_score",
                "login_days",
                "updated_at",
            ]
        )
        return _to_domain(row)


def _profile_details(row: UserProfile) -> ProfileData:
    return ProfileData(
        user_id=row.user_id,
        username=row.user.username,
        name=row.user.get_full_name().strip(),
        email=row.user.email,
        team=slugify(row.group.name) if row.group_id else "",
        avatar=row.avatar,
        scores=dict(row.scores),
        total_score=row.total_score,
        login_days=list(row.login_days),
    )


class DjangoProfileDetailsRepository(ProfileDetailsRepository):
    def get_by_user_id(self, user_id: int) -> ProfileData | None:
        row = (
            UserProfile.objects.select_related("user", "group")
            .filter(user_id=user_id)
            .first()
        )
        return None if row is None else _profile_details(row)

    def get_by_username(
        self, username: str, *, for_update: bool = False
    ) -> ProfileData | None:
        query = UserProfile.objects.select_related("user", "group")
        if for_update:
            # Only lock non-nullable relations; a profile may have no group.
            query = UserProfile.objects.select_related("user").select_for_update()
        row = query.filter(user__username=username).first()
        return None if row is None else _profile_details(row)

    def update(
        self, user_id: int, changes: ProfileChanges, *, group_id: int | None
    ) -> ProfileData:
        row = UserProfile.objects.select_related("user", "group").get(user_id=user_id)
        user_fields = []
        if changes.name is not None:
            row.user.first_name = changes.name
            row.user.last_name = ""
            user_fields.extend(("first_name", "last_name"))
        if changes.email is not None:
            row.user.email = changes.email
            user_fields.append("email")
        if user_fields:
            row.user.save(update_fields=user_fields)
        profile_fields = ["updated_at"]
        if changes.avatar is not None:
            row.avatar = changes.avatar
            profile_fields.append("avatar")
        if changes.team is not None:
            row.group_id = group_id
            profile_fields.append("group")
        row.save(update_fields=profile_fields)
        return _profile_details(row)


class DjangoTeamRepository(TeamRepository):
    def find_by_slug(self, slug: str) -> Sequence[int]:
        return [
            group.pk
            for group in Group.objects.order_by("pk")
            if slugify(group.name) == slug
        ]
