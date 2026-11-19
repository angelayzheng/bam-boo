from dataclasses import dataclass
from datetime import date
from typing import Mapping

from .conversation_node import ConversationNode


@dataclass(frozen=True, slots=True)
class Challenge:
    name: str
    slug: str
    challenge_date: date
    difficulty: int
    category: str
    tone: str
    required_action: str
    conversation_tree: ConversationNode | None = None

    def __post_init__(self):
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError("Challenge name must not be empty.")
        if not isinstance(self.slug, str) or not self.slug.strip():
            raise ValueError("Challenge slug must not be empty.")
        if not isinstance(self.challenge_date, date):
            raise ValueError("Challenge date must be a date.")
        if (
            isinstance(self.difficulty, bool)
            or not isinstance(self.difficulty, int)
            or not 1 <= self.difficulty <= 5
        ):
            raise ValueError("Challenge difficulty must be between 1 and 5.")
        if not isinstance(self.tone, str) or not self.tone.strip():
            raise ValueError("Challenge tone must not be empty.")
        if (
            not isinstance(self.required_action, str)
            or not self.required_action.strip()
        ):
            raise ValueError("Challenge required action must not be empty.")

        tree = self.conversation_tree
        if isinstance(tree, Mapping):
            if not tree:
                object.__setattr__(self, "conversation_tree", None)
            else:
                object.__setattr__(
                    self, "conversation_tree", ConversationNode.from_dict(tree)
                )
        elif tree is not None:
            if not isinstance(tree, ConversationNode):
                raise ValueError(
                    "Challenge conversation tree must be a conversation node."
                )
            object.__setattr__(
                self, "conversation_tree", ConversationNode.from_dict(tree.to_dict())
            )
