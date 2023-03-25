from abc import ABC, abstractmethod

from ..api_wrap import UserMessage


class System(ABC):
    """A system for handling incoming user messages."""

    @abstractmethod
    async def enqueue_message(
        self, message: UserMessage, return_failures: bool = False
    ):
        """Called whenever a new user message arrives."""
        pass
