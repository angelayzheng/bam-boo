from collections.abc import Sequence
from datetime import date

from django.utils.text import slugify

from users.domain.profile import Profile
from users.models import UserProfile
from users.use_cases.ports import ProfileRepository


def _to_domain(row: UserProfile) -> Profile:
    return Profile(
        user_id=row.user_id,
        username=row.user.username,
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
