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
    challenges = Challenge.objects.all()
    category = request.GET.get("category")
    if category:
        challenges = challenges.filter(category=category)
    return JsonResponse({"challenges": [_challenge_summary(c) for c in challenges]})


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
