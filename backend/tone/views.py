import math
import re
import sys
from array import array

from django.http import JsonResponse
from django.views.decorators.http import require_GET

from challenges.models import Challenge

from .models import ToneVector

TONE_SIMILARITY_THRESHOLD = 0.65


def _load_vector(tone):
    # Numberbatch represents phrases using underscores. Prefer that embedding;
    # otherwise average the component words, requiring every word to be known.
    words = re.findall(r"[^\W_]+", tone.casefold())
    phrase = "_".join(words)
    rows = dict(
        ToneVector.objects.filter(word__in={phrase, *words}).values_list(
            "word", "vector"
        )
    )
    keys = [phrase] if phrase in rows else words
    if any(key not in rows for key in keys):
        raise KeyError(tone)
    vectors = []
    for key in keys:
        vector = array("f")
        vector.frombytes(bytes(rows[key]))
        if sys.byteorder != "little":
            vector.byteswap()
        if not vector or not all(math.isfinite(value) for value in vector):
            raise ValueError("Invalid vector.")
        vectors.append(vector)
    if len({len(vector) for vector in vectors}) != 1:
        raise ValueError("Inconsistent vector dimensions.")
    return [sum(values) / len(vectors) for values in zip(*vectors)]


@require_GET
def tone_similarity(request, challenge_id):
    """Grade an answer against the challenge's private, database-backed tone."""
    challenge = Challenge.objects.filter(pk=challenge_id).only("tone").first()
    if challenge is None:
        return JsonResponse({"detail": "Challenge not found."}, status=404)
    answer = request.GET.get("answer", "")
    if len(answer) > 200 or not re.findall(r"[^\W_]+", answer):
        return JsonResponse({"detail": "Enter a tone of 1–200 characters."}, status=400)
    try:
        # A missing reference embedding is a service failure, not an invalid answer.
        second = _load_vector(challenge.tone)
    except KeyError, ValueError:
        return JsonResponse({"detail": "Tone scoring is unavailable."}, status=503)
    try:
        first = _load_vector(answer)
        if len(first) != len(second):
            raise ValueError("Inconsistent vector dimensions.")
        denominator = math.hypot(*first) * math.hypot(*second)
        if not denominator:
            raise ValueError("Zero vector.")
        similarity = math.fsum(a * b for a, b in zip(first, second)) / denominator
    except KeyError:
        return JsonResponse(
            {"detail": "Unknown tone. Try another word or phrase."}, status=404
        )
    except ValueError:
        return JsonResponse({"detail": "Tone scoring is unavailable."}, status=503)
    similarity = max(-1.0, min(1.0, similarity))
    return JsonResponse(
        {"similarity": similarity, "correct": similarity >= TONE_SIMILARITY_THRESHOLD}
    )
