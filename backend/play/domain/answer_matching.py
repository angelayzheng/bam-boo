import re
from math import isfinite


class AnswerMatching:
    TONE_SIMILARITY_THRESHOLD = 0.65

    @classmethod
    def tone_is_correct(cls, similarity):
        if isinstance(similarity, bool) or not isinstance(similarity, (int, float)):
            raise ValueError("Tone similarity must be a finite number.")
        if not isfinite(similarity):
            raise ValueError("Tone similarity must be a finite number.")
        return similarity >= cls.TONE_SIMILARITY_THRESHOLD

    @staticmethod
    def action_is_correct(required_action, answer):
        if not isinstance(required_action, str) or not isinstance(answer, str):
            raise ValueError("Required action and answer must be strings.")
        keywords = re.findall(r"[^\W_]+", required_action.casefold())
        answer_words = set(re.findall(r"[^\W_]+", answer.casefold()))
        return bool(keywords) and all(word in answer_words for word in keywords)
