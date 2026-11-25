from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Mapping

MAX_TREE_DEPTH = 32


@dataclass(frozen=True, slots=True)
class ConversationNode:
    kind: str
    text_file: str
    audio_file: str
    children: tuple["ConversationNode", ...] = ()
    node_key: str | None = None

    def __post_init__(self):
        if not isinstance(self.kind, str) or self.kind not in {
            "question",
            "response",
        }:
            raise ValueError("Conversation node type must be 'question' or 'response'.")
        _validate_media_filename(self.text_file, ".txt")
        _validate_media_filename(self.audio_file, ".mp3")
        if self.node_key is not None and (
            not isinstance(self.node_key, str) or not self.node_key.strip()
        ):
            raise ValueError("Conversation node key must not be empty.")
        if not isinstance(self.children, (list, tuple)):
            raise ValueError("Conversation node children must be a sequence.")
        children = tuple(self.children)
        if any(not isinstance(child, ConversationNode) for child in children):
            raise ValueError("Conversation node children must be conversation nodes.")
        object.__setattr__(self, "children", children)
        expected_kind = "response" if self.kind == "question" else "question"
        if any(child.kind != expected_kind for child in children):
            raise ValueError("Conversation node types must alternate.")

    @classmethod
    def from_dict(cls, data: Mapping, *, _depth=0, _seen_keys=None):
        if not isinstance(data, Mapping):
            raise ValueError("Conversation tree node must be an object.")
        if _depth > MAX_TREE_DEPTH:
            raise ValueError(
                f"Conversation tree exceeds max depth of {MAX_TREE_DEPTH}."
            )
        expected_kind = "question" if _depth % 2 == 0 else "response"
        kind = data.get("type")
        if kind != expected_kind:
            raise ValueError(f"Expected a '{expected_kind}' node, got {kind!r}.")
        children = data.get("children", [])
        if not isinstance(children, list):
            raise ValueError("Conversation node children must be a list.")

        seen_keys = _seen_keys if _seen_keys is not None else set()
        node_key = data.get("node_key")
        if node_key is not None:
            if not isinstance(node_key, str) or not node_key.strip():
                raise ValueError("Conversation node key must be a non-empty string.")
            if node_key in seen_keys:
                raise ValueError(f"Duplicate conversation node key: {node_key!r}.")
            seen_keys.add(node_key)

        return cls(
            kind=kind,
            text_file=data.get("text_file"),
            audio_file=data.get("audio_file"),
            node_key=node_key,
            children=tuple(
                cls.from_dict(child, _depth=_depth + 1, _seen_keys=seen_keys)
                for child in children
            ),
        )

    def to_dict(self):
        result = {
            "type": self.kind,
            "text_file": self.text_file,
            "audio_file": self.audio_file,
            "children": [child.to_dict() for child in self.children],
        }
        if self.node_key is not None:
            result["node_key"] = self.node_key
        return result


def _validate_media_filename(value, suffix):
    if not isinstance(value, str) or not value:
        raise ValueError(f"Media filename must be a non-empty path ending in {suffix}.")
    path = PurePosixPath(value)
    if (
        value != value.strip()
        or "\\" in value
        or path.is_absolute()
        or ".." in path.parts
        or not value.lower().endswith(suffix)
    ):
        raise ValueError(f"Invalid media filename: {value!r}.")
