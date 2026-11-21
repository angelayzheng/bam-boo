import math
import re
import sys
from array import array

from tone.models import ToneVector

from play.use_cases.manage_challenge_run.errors import (
    ToneAnswerUnknown,
    ToneUnavailable,
)


def _normalized_words(text):
    return re.sub(r"[^\w\s-]", " ", text.casefold()).split()


class VectorToneMatcher:
    threshold = 0.65

    @staticmethod
    def _decode(blob):
        try:
            values = array("f")
            values.frombytes(bytes(blob))
            if sys.byteorder != "little":
                values.byteswap()
        except (TypeError, ValueError) as exc:
            raise ToneUnavailable("Tone vectors are invalid.") from exc
        decoded = list(values)
        if not decoded or not all(math.isfinite(value) for value in decoded):
            raise ToneUnavailable("Tone vectors are invalid.")
        return decoded

    def similarity(self, answer, reference):
        if not ToneVector.objects.exists():
            raise ToneUnavailable("Tone vectors are unavailable.")

        def vector_for(text, *, answer_vector):
            words = _normalized_words(text)
            if not words:
                raise ToneAnswerUnknown("Unknown tone answer.")
            phrase = "_".join(words)
            row = ToneVector.objects.filter(word=phrase).first()
            if row is not None:
                return self._decode(row.vector)
            vectors = []
            for word in words:
                row = ToneVector.objects.filter(word=word).first()
                if row is None:
                    if answer_vector:
                        raise ToneAnswerUnknown("Unknown tone answer.")
                    raise ToneUnavailable("Reference tone vector is unavailable.")
                vectors.append(self._decode(row.vector))
            if not vectors or len({len(vector) for vector in vectors}) != 1:
                raise ToneUnavailable("Tone vectors are invalid.")
            return [
                sum(row[i] for row in vectors) / len(vectors)
                for i in range(len(vectors[0]))
            ]

        first = vector_for(answer, answer_vector=True)
        second = vector_for(reference, answer_vector=False)
        if len(first) != len(second):
            raise ToneUnavailable("Tone vectors have different dimensions.")
        first_norm = math.sqrt(sum(value * value for value in first))
        second_norm = math.sqrt(sum(value * value for value in second))
        if (
            not first_norm
            or not second_norm
            or not all(math.isfinite(value) for value in first + second)
        ):
            raise ToneUnavailable("Tone vectors are invalid.")
        return sum(a * b for a, b in zip(first, second)) / (first_norm * second_norm)
