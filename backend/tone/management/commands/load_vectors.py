"""Load ConceptNet Numberbatch word embeddings into the tone table."""

import gzip
import sys
from array import array
from pathlib import Path
from urllib.request import urlretrieve

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from tone.models import ToneVector

VECTORS_URL = "https://conceptnet.s3.amazonaws.com/downloads/2019/numberbatch/numberbatch-en-19.08.txt.gz"
FILENAME = "numberbatch-en-19.08.txt.gz"
BATCH_SIZE = 5_000


def _vector_bytes(values: list[str]) -> bytes:
    """Convert a list of float strings to a little-endian binary blob."""
    vector = array("f", (float(value) for value in values))
    if sys.byteorder != "little":
        vector.byteswap()
    return vector.tobytes()


class Command(BaseCommand):
    help = "Load ConceptNet Numberbatch word vectors into the tone table."

    def add_arguments(self, parser):
        parser.add_argument(
            "--file",
            type=str,
            default=None,
            help=(
                f"Path to {FILENAME} (default: <repo root>/data/{FILENAME}). "
                "Downloaded from ConceptNet S3 if it does not exist."
            ),
        )
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Delete all existing rows before loading.",
        )

    def handle(self, *args, **options):
        data_path = (
            Path(options["file"])
            if options["file"]
            # BASE_DIR is backend/, so its parent is the repo root.
            else Path(settings.BASE_DIR).parent / "data" / FILENAME
        )

        count, expected_count = self._setup(data_path, clear=options["clear"])

        if count != expected_count:
            self.stderr.write(
                self.style.WARNING(
                    f"Header declares {expected_count:,} vectors but read {count:,}."
                )
            )

        self.stdout.write(
            self.style.SUCCESS(f"Loaded {count:,} word vectors into the tone table.")
        )

    @staticmethod
    def _download(data_path: Path) -> None:
        """Download to a temp file, then rename, so a failed download never
        leaves a corrupt file at the final path."""
        data_path.parent.mkdir(parents=True, exist_ok=True)
        partial_path = data_path.with_name(data_path.name + ".part")
        try:
            urlretrieve(VECTORS_URL, partial_path)
            partial_path.replace(data_path)
        except BaseException:
            partial_path.unlink(missing_ok=True)
            raise

    def _setup(self, data_path: Path, clear: bool) -> tuple[int, int]:
        """Download the vector file if needed, then load it into the database."""
        if not data_path.exists():
            self.stdout.write(f"Downloading Numberbatch vectors to {data_path}...")
            self._download(data_path)
            self.stdout.write(self.style.SUCCESS("Download complete."))

        # Keep database changes atomic so a failed load rolls back --clear too.
        with transaction.atomic():
            return self._load_vectors(data_path, clear=clear)

    def _load_vectors(self, data_path: Path, clear: bool) -> tuple[int, int]:
        """Stream an existing file into the database; return loaded and expected counts."""
        if not data_path.exists():
            raise CommandError(f"Numberbatch file does not exist: {data_path}")

        if clear:
            deleted, _ = ToneVector.objects.all().delete()
            self.stdout.write(f"Cleared {deleted} existing rows.")

        self.stdout.write(
            f"Reading vectors from {data_path.name}... (may take a while)"
        )
        count = 0
        batch = []

        with gzip.open(data_path, "rt", encoding="utf-8") as vectors_file:
            header = vectors_file.readline().split()
            if len(header) != 2:
                raise CommandError("Numberbatch file has an invalid header.")
            expected_count, dimension = map(int, header)

            for line_number, line in enumerate(vectors_file, start=2):
                parts = line.split()
                if len(parts) != dimension + 1:
                    raise CommandError(
                        f"Invalid vector on line {line_number}: "
                        f"expected {dimension} values."
                    )
                word = parts[0]
                blob = _vector_bytes(parts[1:])
                batch.append(ToneVector(word=word, vector=blob))
                count += 1

                if len(batch) >= BATCH_SIZE:
                    ToneVector.objects.bulk_create(
                        batch,
                        update_conflicts=True,
                        unique_fields=["word"],
                        update_fields=["vector"],
                    )
                    batch.clear()
                    if count % 50_000 == 0:
                        self.stdout.write(f"  {count:,} vectors loaded...")

            if batch:
                ToneVector.objects.bulk_create(
                    batch,
                    update_conflicts=True,
                    unique_fields=["word"],
                    update_fields=["vector"],
                )

        return count, expected_count
