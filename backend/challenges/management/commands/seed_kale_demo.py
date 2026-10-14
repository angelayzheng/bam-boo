"""Seed the 'Forgot Password x3' demo challenge from the bundled seed data.

The seed directory holds one ``Transcript.txt`` (customer lines ``C1``-``C7``,
a blank line, then agent lines ``A1``-``A6``) plus one ``.mp3`` per line.
This command splits the transcript into per-turn ``.txt`` files, copies each
turn's files into the challenge media directory, and stores the branching
alternating conversation tree as bare filename pairs::

    C1 -> A1 -> C2 -> A4 -> C5
    C1 -> A2 -> C3 -> A5 -> C6
    C1 -> A3 -> C4 -> A6 -> C7
"""

import shutil
from datetime import date
from pathlib import Path

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.management.base import BaseCommand, CommandError

from challenges.models import Challenge

SEED_DIR = Path(__file__).resolve().parent.parent.parent / "source_data" / "kale_demo"
CHALLENGE_SLUG = "forgot-password-x3"

# Branching conversation paths after the shared C1 opener. Each path lists
# node keys from the agent reply down to the closing customer line.
BRANCHES = [
    ("a1", "c2", "a4", "c5"),
    ("a2", "c3", "a5", "c6"),
    ("a3", "c4", "a6", "c7"),
]


def _media_path(*parts):
    return "/".join(["challenges", CHALLENGE_SLUG, *parts])


def _read_turns(demo_dir):
    transcript = demo_dir / "Transcript.txt"
    if not transcript.is_file():
        raise CommandError(f"Missing transcript: {transcript}")
    blocks = [
        [line.strip() for line in block.splitlines() if line.strip()]
        for block in transcript.read_text(encoding="utf-8").split("\n\n")
    ]
    blocks = [block for block in blocks if block]
    if len(blocks) != 2:
        raise CommandError(
            "Expected two transcript blocks (customer, blank line, agent), "
            f"found {len(blocks)}."
        )
    customer_lines, agent_lines = blocks
    if len(customer_lines) != 7 or len(agent_lines) != 6:
        raise CommandError(
            "Expected 7 customer lines and 6 agent lines, found "
            f"{len(customer_lines)} and {len(agent_lines)}."
        )
    turns = {f"c{index}": text for index, text in enumerate(customer_lines, start=1)}
    turns.update({f"a{index}": text for index, text in enumerate(agent_lines, start=1)})

    expected_keys = {"c1"} | {key for branch in BRANCHES for key in branch}
    if set(turns) != expected_keys:
        raise CommandError(
            f"Transcript lines do not cover tree node keys {sorted(expected_keys)}."
        )
    for node_key in turns:
        audio = demo_dir / f"{node_key.upper()}.mp3"
        if not audio.is_file():
            raise CommandError(f"Missing audio file: {audio}")
    return turns


class Command(BaseCommand):
    help = "Seed the 'Forgot Password x3' demo challenge from bundled seed data."

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Delete and rebuild the demo challenge if it already exists.",
        )

    def handle(self, *args, **options):
        demo_dir = SEED_DIR
        if not demo_dir.is_dir():
            raise CommandError(f"Demo directory not found: {demo_dir}")
        turns = _read_turns(demo_dir)

        existing = Challenge.objects.filter(slug=CHALLENGE_SLUG).first()
        if existing is not None and not options["force"]:
            self.stdout.write(
                f"Challenge '{existing.name}' already exists; use --force to rebuild."
            )
            return
        if existing is not None:
            existing.delete()
        media_dir = Path(settings.MEDIA_ROOT) / "challenges" / CHALLENGE_SLUG
        if media_dir.exists():
            shutil.rmtree(media_dir)

        nodes = {}
        for node_key, text in turns.items():
            kind = "question" if node_key.startswith("c") else "response"
            text_name = _media_path(kind, f"{node_key}.txt")
            audio_name = _media_path(kind, f"{node_key}.mp3")
            default_storage.save(text_name, ContentFile(text + "\n"))
            audio_path = demo_dir / f"{node_key.upper()}.mp3"
            with audio_path.open("rb") as audio_file:
                default_storage.save(audio_name, ContentFile(audio_file.read()))
            nodes[node_key] = {
                "type": kind,
                "node_key": node_key,
                "text_file": text_name,
                "audio_file": audio_name,
                "children": [],
            }

        for branch in BRANCHES:
            nodes["c1"]["children"].append(nodes[branch[0]])
            for parent_key, child_key in zip(branch, branch[1:]):
                nodes[parent_key]["children"].append(nodes[child_key])

        challenge = Challenge.objects.create(
            name="Forgot Password x3",
            slug=CHALLENGE_SLUG,
            challenge_date=date.today(),
            difficulty=1,
            category="account",
            tone="frustrated",
            required_action="reset password",
            conversation_tree=nodes["c1"],
        )

        self.stdout.write(
            self.style.SUCCESS(f"Seeded '{challenge.name}' with {len(nodes)} turns.")
        )
