"""Presenter for the browse-challenges use case.

Turns BrowseChallengesOutputData into a JSON-ready dict (or an error message)
that the Django view returns. Implements the output boundary.
"""

from challenges.use_cases.BrowseChallenges.BrowseChallengesOutputBoundary import (
    BrowseChallengesOutputBoundary,
)


class BrowseChallengesPresenter(BrowseChallengesOutputBoundary):
    def __init__(self):
        self.payload = None
        self.error = None

    def prepare_success_view(self, output):
        self.payload = {
            "year": output.year,
            "month": output.month,
            "days": [
                {
                    "date": d.date.isoformat(),
                    "status": d.status,
                    "stars": d.stars,
                    "slug": d.slug,
                    "name": d.name,
                    "difficulty": d.difficulty,
                    "category": d.category,
                }
                for d in output.days
            ],
        }

    def prepare_fail_view(self, message):
        self.error = message
