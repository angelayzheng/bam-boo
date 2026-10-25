from django.http import JsonResponse
from django.views.decorators.http import require_GET


@require_GET
def tone_similarity(request, tone1, tone2):
    """GET /api/tone/<tone1>&<tone2>/: return a similarity score."""
    # The implementation is intentionally commented out while the similarity
    # normalization rules are finalized.
    #
    # def _load_vector(word):
    #     row = ToneVector.objects.filter(word=word).first()
    #     if row is None:
    #         return None
    #     vector = array("f")
    #     vector.frombytes(bytes(row.vector))
    #     if sys.byteorder != "little":
    #         vector.byteswap()
    #     return vector
    #
    # first = _load_vector(tone1)
    # second = _load_vector(tone2)
    # if first is None or second is None:
    #     return JsonResponse({"detail": "Unknown tone."}, status=404)
    # similarity = sum(a * b for a, b in zip(first, second)) / (
    #     (sum(a * a for a in first) ** 0.5)
    #     * (sum(b * b for b in second) ** 0.5)
    # )
    # return JsonResponse({"similarity": max(0.0, min(1.0, similarity))})
    return JsonResponse({"detail": "Not implemented."}, status=501)
