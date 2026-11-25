"""Input boundary for the browse-challenges use case.

The interface the controller calls to ask for a month of calendar data.
Implemented by BrowseChallengesInteractor, so the controller depends on this
abstraction and never on the interactor itself.
"""

from abc import ABC, abstractmethod

from .InputData import BrowseChallengesInputData


class BrowseChallengesInputBoundary(ABC):
    @abstractmethod
    def execute(self, input_data: BrowseChallengesInputData) -> None: ...
