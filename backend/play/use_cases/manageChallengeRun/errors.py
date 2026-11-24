class ToneAnswerUnknown(Exception):
    """The submitted tone has no usable vector representation."""


class ToneUnavailable(Exception):
    """Tone vectors cannot be used to grade this answer."""
