import json

from config.container import get_container
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST


def _json_body(request, controller):
    if request.content_type != "application/json":
        controller.reject_input("Expected an application/json body.")
        return None
    try:
        value = json.loads(request.body)
    except ValueError, UnicodeDecodeError:
        controller.reject_input("Expected a valid JSON object.")
        return None
    if not isinstance(value, dict):
        controller.reject_input("Expected a JSON object.")
        return None
    return value


def _response(use_case):
    return JsonResponse(
        use_case.presenter.response_body,
        status=use_case.presenter.status_code,
    )


def _user_id(request):
    return request.user.pk if request.user.is_authenticated else None


@require_POST
def start_challenge(request, slug):
    """POST /api/challenges/<slug>/attempts/: start a challenge run."""
    use_case = get_container().build_manage_challenge_run_use_case()
    payload = _json_body(request, use_case.controller)
    if payload is not None:
        use_case.controller.start_challenge(slug, _user_id(request), payload)
    return _response(use_case)


@require_GET
def get_run(request, attempt_id):
    """GET /api/attempts/<uuid>/: return the current run snapshot."""
    use_case = get_container().build_manage_challenge_run_use_case()
    use_case.controller.get_run(str(attempt_id), _user_id(request))
    return _response(use_case)


def _transition_view(request, attempt_id, controller_method):
    use_case = get_container().build_manage_challenge_run_use_case()
    payload = _json_body(request, use_case.controller)
    if payload is not None:
        getattr(use_case.controller, controller_method)(
            str(attempt_id), _user_id(request), payload
        )
    return _response(use_case)


@require_POST
def submit_tone(request, attempt_id):
    """POST /api/attempts/<uuid>/tone/: grade the tone answer."""
    return _transition_view(request, attempt_id, "submit_tone")


@require_POST
def choose_response(request, attempt_id):
    """POST /api/attempts/<uuid>/choices/: select a response."""
    return _transition_view(request, attempt_id, "choose_response")


@require_POST
def continue_conversation(request, attempt_id):
    """POST /api/attempts/<uuid>/continue/: advance the conversation."""
    return _transition_view(request, attempt_id, "continue_conversation")


@require_POST
def submit_action(request, attempt_id):
    """POST /api/attempts/<uuid>/action/: grade and complete a challenge run."""
    return _transition_view(request, attempt_id, "submit_action")
