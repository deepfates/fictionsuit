from abc import ABC, abstractmethod

from .user_message import UserMessage


class System(ABC):
    """A system for handling incoming user messages."""

    @abstractmethod
    async def enqueue_message(
        self,
        message: UserMessage,
        return_failures: bool = False,
        return_returns: bool = False,
        return_whatever: bool = False,
    ):
        """Called whenever a new user message arrives."""
        pass
