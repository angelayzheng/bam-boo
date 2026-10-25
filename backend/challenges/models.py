from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class ChallengeCategory(models.TextChoices):
    WORK = "work", "Work"
    SOCIAL = "social", "Social"
    FAMILY = "family", "Family"
    HEALTH = "health", "Health"
    EMERGENCY = "emergency", "Emergency"
    ACCOUNT_HELP = "account", "Account Help"
    OTHER = "other", "Other"


class NodeKind(models.TextChoices):
    QUESTION = "question", "Question"
    RESPONSE = "response", "Response"


MAX_TREE_DEPTH = 32


def _validate_media_filename(value, *, suffix):
    if not isinstance(value, str) or not value:
        raise ValidationError(f"Must be a non-empty path ending in {suffix}.")
    if value != value.strip():
        raise ValidationError("Filename must not have leading/trailing whitespace.")
    if value.startswith("/") or ".." in value.split("/"):
        raise ValidationError("Filename must be a relative path without '..'.")
    if not value.lower().endswith(suffix):
        raise ValidationError(f"Filename must end in {suffix}.")


def validate_conversation_tree(tree):
    """Validate the question/response conversation tree.

    Expected shape::

        {
            "type": "question",
            "text_file": "challenges/<slug>/transcripts/q1.txt",
            "audio_file": "challenges/<slug>/audio/q1.mp3",
            "children": [
                {
                    "type": "response",
                    "text_file": "...",
                    "audio_file": "...",
                    "children": [ ... questions ... ],
                },
            ],
        }

    Layers must alternate between questions and responses, starting with a
    question at the root. Every node references one transcript (.txt) and one
    audio (.mp3) file stored under the challenge media directory.
    """
    if not isinstance(tree, dict):
        raise ValidationError("Conversation tree must be a JSON object.")

    def _check_node(node, expected_kind, depth, seen_keys):
        if not isinstance(node, dict):
            raise ValidationError("Each tree node must be a JSON object.")
        kind = node.get("type")
        if kind != expected_kind:
            raise ValidationError(f"Expected a '{expected_kind}' node, got {kind!r}.")
        if depth > MAX_TREE_DEPTH:
            raise ValidationError(
                f"Conversation tree exceeds max depth of {MAX_TREE_DEPTH}."
            )
        _validate_media_filename(node.get("text_file"), suffix=".txt")
        _validate_media_filename(node.get("audio_file"), suffix=".mp3")

        node_key = node.get("node_key")
        if node_key is not None:
            if not isinstance(node_key, str) or not node_key.strip():
                raise ValidationError("node_key must be a non-empty string.")
            if node_key in seen_keys:
                raise ValidationError(f"Duplicate node_key: {node_key!r}.")
            seen_keys.add(node_key)

        children = node.get("children", [])
        if not isinstance(children, list):
            raise ValidationError("'children' must be a list.")
        next_kind = (
            NodeKind.RESPONSE
            if expected_kind == NodeKind.QUESTION
            else NodeKind.QUESTION
        )
        for child in children:
            _check_node(child, next_kind, depth + 1, seen_keys)

    _check_node(tree, NodeKind.QUESTION, 0, set())


class Challenge(models.Model):
    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=120, unique=True)
    challenge_date = models.DateField(db_index=True)
    difficulty = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    category = models.CharField(
        max_length=32, choices=ChallengeCategory.choices, db_index=True
    )
    tone = models.CharField(max_length=64)
    required_action = models.TextField()
    conversation_tree = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-challenge_date", "name"]
        indexes = [
            models.Index(fields=["category", "difficulty"]),
        ]

    def __str__(self):
        return self.name

    def clean(self):
        super().clean()
        if self.conversation_tree:
            validate_conversation_tree(self.conversation_tree)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
