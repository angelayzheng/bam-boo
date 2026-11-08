from datetime import date
from difflib import SequenceMatcher

from django.http import JsonResponse
from django.views.decorators.http import require_GET

from .models import Challenge, ChallengeCategory
from .serialization import tree_with_urls

NAME_MATCH_THRESHOLD = 0.6


def _challenge_summary(challenge):
    return {
        "name": challenge.name,
        "slug": challenge.slug,
        "challenge_date": challenge.challenge_date.isoformat(),
        "difficulty": challenge.difficulty,
        "category": challenge.category,
    }


def _challenge_detail(challenge):
    payload = _challenge_summary(challenge)
    tree = challenge.conversation_tree or {}
    payload.update(
        {
            "tone": challenge.tone,
            "required_action": challenge.required_action,
            "conversation_tree": tree_with_urls(tree) if tree else {},
        }
    )
    return payload


def _filter_challenges(request):
    challenges = Challenge.objects.all()
    category = request.GET.get("category")
    if category:
        if category not in ChallengeCategory.values:
            return None, JsonResponse(
                {"detail": "Invalid category filter."}, status=400
            )
        challenges = challenges.filter(category=category)

    raw_date = request.GET.get("date")
    if raw_date:
        try:
            challenge_date = date.fromisoformat(raw_date)
        except ValueError:
            return None, JsonResponse(
                {"detail": "Invalid date filter; expected YYYY-MM-DD."}, status=400
            )
        challenges = challenges.filter(challenge_date=challenge_date)

    raw_difficulty = request.GET.get("difficulty")
    if raw_difficulty:
        try:
            difficulty = int(raw_difficulty)
        except ValueError:
            return None, JsonResponse(
                {"detail": "Invalid difficulty filter; expected an integer."},
                status=400,
            )
        if not 1 <= difficulty <= 5:
            return None, JsonResponse(
                {
                    "detail": "Invalid difficulty filter; expected an integer from 1 to 5."
                },
                status=400,
            )
        challenges = challenges.filter(difficulty=difficulty)

    return challenges, None


def _fuzzy_match_by_name(challenges, name):
    normalized = name.strip().casefold()
    if not normalized:
        return challenges
    scored = []
    for challenge in challenges:
        score = SequenceMatcher(None, normalized, challenge.name.casefold()).ratio()
        if score >= NAME_MATCH_THRESHOLD:
            scored.append((score, challenge))
    scored.sort(
        key=lambda pair: (
            -pair[0],
            -pair[1].challenge_date.toordinal(),
            pair[1].name.casefold(),
        )
    )
    return [challenge for _, challenge in scored]


@require_GET
def challenge_list(request):
    """GET /api/challenges/?category=...&name=...&date=...&difficulty=..."""
    challenges, error = _filter_challenges(request)
    if error is not None:
        return error
    name = request.GET.get("name")
    if name:
        challenges = _fuzzy_match_by_name(challenges, name)
    return JsonResponse({"challenges": [_challenge_summary(c) for c in challenges]})


@require_GET
def challenge_detail(request, slug):
    """GET /api/challenges/<slug>/: return one challenge by slug."""
    challenge = Challenge.objects.filter(slug=slug).first()
    if challenge is None:
        return JsonResponse({"detail": "Challenge not found."}, status=404)
    return JsonResponse(_challenge_detail(challenge))
