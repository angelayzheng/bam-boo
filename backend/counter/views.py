import json

from django.db import transaction
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .models import Counter


def _get_counter():
    counter, _ = Counter.objects.get_or_create(key="main")
    return counter


@csrf_exempt
def count(request):
    if request.method == "GET":
        return JsonResponse({"count": _get_counter().value})

    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    try:
        payload = json.loads(request.body or "{}")
        delta = int(payload["delta"])
    except KeyError, TypeError, ValueError, json.JSONDecodeError:
        return JsonResponse({"error": "delta must be an integer"}, status=400)

    if delta not in (-1, 1):
        return JsonResponse({"error": "delta must be -1 or 1"}, status=400)

    with transaction.atomic():
        counter = Counter.objects.select_for_update().get_or_create(key="main")[0]
        counter.value += delta
        counter.save(update_fields=["value", "updated_at"])

    return JsonResponse({"count": counter.value})
