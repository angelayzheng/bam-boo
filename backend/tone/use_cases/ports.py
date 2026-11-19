from collections.abc import Sequence
from typing import Protocol


class ToneVectorRepository(Protocol):
    def get_vector(self, word: str) -> Sequence[float] | None: ...
