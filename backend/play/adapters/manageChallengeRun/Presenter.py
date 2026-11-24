from challenges.serialization import media_url
from play.use_cases.manageChallengeRun.OutputBoundary import (
    ManageChallengeRunOutputBoundary,
)
from play.use_cases.manageChallengeRun.OutputData import (
    PlayFailureData,
    PlayFailureReason,
    PlaySuccessData,
)


class ChallengeRunPresenter(ManageChallengeRunOutputBoundary):
    _FAILURE_STATUS_CODES = {
        PlayFailureReason.INVALID_INPUT: 400,
        PlayFailureReason.CHALLENGE_NOT_FOUND: 404,
        PlayFailureReason.CHALLENGE_UNAVAILABLE: 409,
        PlayFailureReason.RUN_NOT_FOUND: 404,
        PlayFailureReason.RUN_FORBIDDEN: 403,
        PlayFailureReason.INVALID_STAGE: 409,
        PlayFailureReason.UNKNOWN_TONE_ANSWER: 422,
        PlayFailureReason.TONE_UNAVAILABLE: 503,
        PlayFailureReason.PROFILE_NOT_FOUND: 404,
        PlayFailureReason.ATTEMPT_CONFLICT: 409,
    }

    def __init__(self):
        self.response_body: dict = {}
        self.status_code = 200

    def prepare_success_view(self, output_data: PlaySuccessData) -> None:
        self.response_body = _snapshot(output_data.run, output_data.challenge)
        self.status_code = output_data.status_code

    def prepare_fail_view(self, failure: PlayFailureData) -> None:
        self.response_body = {"detail": failure.message}
        self.status_code = self._FAILURE_STATUS_CODES[failure.reason]


def _snapshot(run, challenge):
    root = challenge.conversation_tree
    nodes = _node_map(root)
    history = [_present_node(nodes[key]) for key in run.conversation]
    if run.stage == "tone":
        choices = []
    else:
        current = nodes.get(run.current_node, root)
        choices = [
            _present_node(node, index)
            for index, node in enumerate(current.children)
            if node.kind == "response"
        ]
    payload = {
        "attempt_id": run.id,
        "stage": run.stage,
        "challenge": {
            "name": challenge.name,
            "slug": challenge.slug,
            "challenge_date": challenge.challenge_date.isoformat(),
            "difficulty": challenge.difficulty,
            "category": challenge.category,
        },
        "opening": _present_node(root),
        "conversation": history,
        "choices": choices,
        "tone_correct": run.tone_correct,
        "tone_time": run.tone_time,
        "tone_speed_correct": (
            run.tone_time <= 10 if run.tone_time is not None else None
        ),
    }
    if run.tone_similarity is not None:
        payload["tone_similarity"] = run.tone_similarity
    if run.stage == "completed":
        payload.update(
            {
                "action_correct": run.action_correct,
                "score": run.score,
                "required_action": challenge.required_action,
                "completed_at": run.completed_at.isoformat(),
                "user_id": run.user_id,
                "saved": run.user_id is not None,
            }
        )
    return payload


def _node_map(root):
    result = {}

    def visit(node):
        if node.node_key is not None:
            result[node.node_key] = node
        for child in node.children:
            visit(child)

    visit(root)
    return result


def _present_node(node, choice_id=None):
    result = {
        "id": node.node_key,
        "type": node.kind,
        "transcript_url": media_url(node.text_file),
        "audio_url": media_url(node.audio_file),
    }
    if choice_id is not None:
        result["choice_id"] = str(choice_id)
    return result
