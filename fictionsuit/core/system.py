from abc import ABC, abstractmethod
from ..api_wrap.user_message import UserMessage


class System(ABC):
    """A system for handling incoming user messages."""

    @abstractmethod
    async def enqueue_message(self, message: UserMessage):
        """Called whenever a new user message arrives."""
        pass
