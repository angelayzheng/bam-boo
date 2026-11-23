from dataclasses import dataclass, field
from datetime import datetime


@dataclass(slots=True)
class Run:
    id: str
    challenge_slug: str
    current_node: str
    created_at: datetime
    user_id: int | None = None
    stage: str = "tone"
    conversation: list[str] = field(default_factory=list)
    tone_correct: bool | None = None
    tone_time: float | None = None
    tone_similarity: float | None = None
    action_correct: bool | None = None
    score: int | None = None
    completed_at: datetime | None = None

    def __post_init__(self):
        if not isinstance(self.id, str) or not self.id.strip():
            raise ValueError("Run ID must not be empty.")
        if not isinstance(self.challenge_slug, str) or not self.challenge_slug.strip():
            raise ValueError("Run challenge slug must not be empty.")
        if not isinstance(self.current_node, str) or not self.current_node.strip():
            raise ValueError("Run current node must not be empty.")
        if self.user_id is not None and (
            isinstance(self.user_id, bool) or not isinstance(self.user_id, int)
        ):
            raise ValueError("Run user ID must be an integer or null.")
        if self.stage not in {"tone", "conversation", "action", "completed"}:
            raise ValueError("Run stage is invalid.")
        if not isinstance(self.conversation, list) or any(
            not isinstance(node_key, str) for node_key in self.conversation
        ):
            raise ValueError("Run conversation must be a list of node keys.")
        if (
            not isinstance(self.created_at, datetime)
            or self.created_at.utcoffset() is None
        ):
            raise ValueError("Run creation time must be timezone-aware.")

    def record_tone(
        self,
        similarity: float,
        correct: bool,
        elapsed_seconds: float,
        root_node: str,
    ):
        self.tone_similarity = similarity
        self.tone_time = elapsed_seconds
        self.tone_correct = correct
        self.stage = "conversation"
        self.current_node = root_node
        self.conversation = [root_node]

    def choose_response(self, response_node, followup_node=None):
        self.conversation = [*self.conversation, response_node.node_key]
        if followup_node is not None:
            self.conversation.append(followup_node.node_key)
            self.current_node = followup_node.node_key
        else:
            self.current_node = response_node.node_key

    def continue_conversation(self):
        self.stage = "action"

    def complete(self, action_correct: bool, score: int, completed_at: datetime):
        self.action_correct = action_correct
        self.score = score
        self.completed_at = completed_at
        self.stage = "completed"
