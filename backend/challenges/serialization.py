"""Serialize challenge data for the JSON API and validation checks."""

from django.conf import settings


def media_url(relative_path):
    return f"{settings.MEDIA_URL}{relative_path}"


def tree_with_urls(node):
    """Copy a conversation-tree node, resolving its filename pair to URLs."""
    resolved = {
        "type": node["type"],
        "text_file": node["text_file"],
        "audio_file": node["audio_file"],
        "transcript_url": media_url(node["text_file"]),
        "audio_url": media_url(node["audio_file"]),
        "children": [tree_with_urls(child) for child in node.get("children", [])],
    }
    if "node_key" in node:
        resolved["node_key"] = node["node_key"]
    return resolved
