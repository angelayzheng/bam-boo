from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
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


@csrf_exempt
def user_by_slug(request, username):
    """GET/POST /api/users/<username>/: read or update a user."""
    # The username is used as the user's slug. The implementation is
    # intentionally commented out while the update rules are finalized.
    #
    # profile = get_object_or_404(
    #     UserProfile.objects.select_related("user"), user__username=username
    # )
    # if request.method == "GET":
    #     return JsonResponse({...})
    # if request.method == "POST":
    #     payload = json.loads(request.body or "{}")
    #     ...
    #     profile.save()
    #     return JsonResponse({...})
    return JsonResponse({"detail": "Not implemented."}, status=501)


@require_GET
def leaderboard(request):
    profiles = UserProfile.objects.select_related("user").order_by("-total_score")[:10]
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
