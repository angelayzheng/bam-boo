from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_GET

from .models import Challenge


def _challenge_summary(challenge):
    return {
        "id": challenge.id,
        "name": challenge.name,
        "slug": challenge.slug,
        "challenge_date": challenge.challenge_date.isoformat(),
        "difficulty": challenge.difficulty,
        "category": challenge.category,
        "tone": challenge.tone,
    }


def _tree_with_urls(node):
    """Copy a conversation-tree node, resolving its filename pair to URLs.

    The database stores bare filename pairs (spec-literal); URL resolution
    happens here so the frontend never hand-builds media paths.
    """
    resolved = {
        "type": node["type"],
        "text_file": node["text_file"],
        "audio_file": node["audio_file"],
        "transcript_url": f"{settings.MEDIA_URL}{node['text_file']}",
        "audio_url": f"{settings.MEDIA_URL}{node['audio_file']}",
        "children": [_tree_with_urls(child) for child in node.get("children", [])],
    }
    if "node_key" in node:
        resolved["node_key"] = node["node_key"]
    return resolved


@require_GET
def challenge_list(request):
    """GET /api/challenges/?category=...&name=...&date=...&difficulty=...

    The base list currently filters by category only; the planned fuzzy and
    strict filters below are intentionally left commented out.
    """
    # Planned fuzzy name search with strict category/date/difficulty filters.
    # The implementation is intentionally commented out until the matching
    # rules are defined.
    #
    # name = request.GET.get("name")
    # date = request.GET.get("date")
    # difficulty = request.GET.get("difficulty")
    # challenges = Challenge.objects.all()
    # if category:
    #     challenges = challenges.filter(category=category)
    # if date:
    #     challenges = challenges.filter(challenge_date=date)
    # if difficulty:
    #     challenges = challenges.filter(difficulty=difficulty)
    # if name:
    #     challenges = _fuzzy_match_by_name(challenges, name)
    # return JsonResponse(
    #     {"challenges": [_challenge_summary(c) for c in challenges]}
    # )
    challenges = Challenge.objects.all()
    category = request.GET.get("category")
    if category:
        challenges = challenges.filter(category=category)
    return JsonResponse({"challenges": [_challenge_summary(c) for c in challenges]})


@require_GET
def challenge_detail_by_slug(request, slug):
    """GET /api/challenges/<slug>/: return one challenge by slug."""
    # The implementation is intentionally commented out while the response
    # shape is finalized.
    #
    # challenge = get_object_or_404(Challenge, slug=slug)
    # payload = _challenge_summary(challenge)
    # payload.update(
    #     {
    #         "required_action": challenge.required_action,
    #         "conversation_tree": _tree_with_urls(challenge.conversation_tree),
    #     }
    # )
    # return JsonResponse(payload)
    return JsonResponse({"detail": "Not implemented."}, status=501)


@require_GET
def challenge_detail(request, challenge_id):
    challenge = get_object_or_404(Challenge, pk=challenge_id)
    payload = _challenge_summary(challenge)
    tree = challenge.conversation_tree or {}
    payload.update(
        {
            "required_action": challenge.required_action,
            "conversation_tree": _tree_with_urls(tree) if tree else {},
        }
    )
    return JsonResponse(payload)
