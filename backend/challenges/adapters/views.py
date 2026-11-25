from datetime import date
from difflib import SequenceMatcher

from django.http import JsonResponse
from django.views.decorators.http import require_GET

from config.container import get_container
from challenges.models import Challenge, ChallengeCategory

from challenges.adapters.browseChallengesDataAccess import (
    DjangoBrowseChallengesDataAccess,
)
from challenges.adapters.browseChallengesPresenter import BrowseChallengesPresenter
from challenges.useCases.browseChallenges.InputData import (
    BrowseChallengesInputData,
)
from challenges.useCases.browseChallenges.Interactor import (
    BrowseChallengesInteractor,
)

NAME_MATCH_THRESHOLD = 0.6


def _challenge_summary(challenge):
    return {
        "name": challenge.name,
        "slug": challenge.slug,
        "challenge_date": challenge.challenge_date.isoformat(),
        "difficulty": challenge.difficulty,
        "category": challenge.category,
    }


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
    """GET /api/challenges/?category={}&name={}&...: list challenges with optional filters."""
    challenges, error = _filter_challenges(request)
    if error is not None:
        return error
    name = request.GET.get("name")
    if name:
        challenges = _fuzzy_match_by_name(challenges, name)
    return JsonResponse({"challenges": [_challenge_summary(c) for c in challenges]})


@require_GET
def challenge_detail(request, slug):
    """GET /api/challenges/<slug>/: return public challenge metadata."""
    use_case = get_container().build_get_challenge_use_case()
    use_case.controller.execute(slug)
    return JsonResponse(
        use_case.presenter.response_body, status=use_case.presenter.status_code
    )


@require_GET
def calendar_view(request):
    """GET /api/calendar/?year=2026&month=10: one month with the user's statuses."""
    try:
        year = int(request.GET["year"])
        month = int(request.GET["month"])
    except KeyError, ValueError:
        return JsonResponse(
            {"detail": "year and month are required integers."}, status=400
        )

    user_id = request.user.id if request.user.is_authenticated else None
    presenter = BrowseChallengesPresenter()
    interactor = BrowseChallengesInteractor(
        DjangoBrowseChallengesDataAccess(), presenter
    )
    interactor.execute(
        BrowseChallengesInputData(year=year, month=month, user_id=user_id)
    )

    if presenter.error is not None:
        return JsonResponse({"detail": presenter.error}, status=400)
    return JsonResponse(presenter.payload)
