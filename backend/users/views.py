from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_GET

from .models import UserProfile


@require_GET
def user_profile(request, user_id):
    profile = get_object_or_404(
        UserProfile.objects.select_related("user"), user__pk=user_id
    )
    return JsonResponse(
        {
            "user_id": profile.user_id,
            "username": profile.user.username,
            "avatar": profile.avatar,
            "total_score": profile.total_score,
            "completed_challenges": len(profile.scores),
            "scores": profile.scores,
        }
    )


@require_GET
def leaderboard(request):
    profiles = UserProfile.objects.select_related("user").order_by("-total_score")[:20]
    return JsonResponse(
        {
            "leaderboard": [
                {
                    "user_id": profile.user_id,
                    "username": profile.user.username,
                    "avatar": profile.avatar,
                    "total_score": profile.total_score,
                }
                for profile in profiles
            ]
        }
    )
