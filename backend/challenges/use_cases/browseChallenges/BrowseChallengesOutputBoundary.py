"""Output boundary for the browse-challenges use case.

The interface the interactor calls to report a result or a failure. The presenter
implements it, so the interactor never knows about JSON, views, or the frontend.
"""

from abc import ABC, abstractmethod

from .BrowseChallengesOutputData import BrowseChallengesOutputData


class BrowseChallengesOutputBoundary(ABC):
    @abstractmethod
    def prepare_success_view(self, output: BrowseChallengesOutputData) -> None: ...

    @abstractmethod
    def prepare_fail_view(self, message: str) -> None: ...
