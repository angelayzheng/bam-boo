class RunNotFound(Exception):
    """The requested run does not exist or cannot be claimed for this challenge."""


class RunForbidden(Exception):
    """The current user does not own the requested run."""
