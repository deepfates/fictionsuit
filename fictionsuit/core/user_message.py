from __future__ import annotations
from abc import ABC, abstractmethod


class UserMessage(ABC):
    MAX_ATTEMPTS = 3

    """Represents a platform-agnostic message from a user."""

    def __init__(self, content: str, author: str):
        self.content = content
        self.author = author
        self.char_limit = -1
        self.disable_interactions = False
        self.no_react = False

    @abstractmethod
    async def _get_timestamp(self) -> float:
        pass

    async def get_timestamp(self) -> float:
        return await self._get_timestamp()

    @abstractmethod
    async def _reply(self, reply_content: str) -> bool:
        """Directly reply to a user message.
        Return True if the reply is sent successfully."""
        pass

    @abstractmethod
    async def _send(self, reply_content: str) -> bool:
        """Send a message on the same platform as the user message.
        Return True if the message is sent successfully."""
        pass

    @abstractmethod
    async def _react(self, reaction: str | None) -> bool:
        """React to the message (e.g. discord emoji reactions, twitter like/rt, etc.)
        Return True if the reaction is applied successfully."""
        pass

    @abstractmethod
    async def _undo_react(self, reaction: str | None) -> bool:
        """Remove a reaction to a message.
        Return True if the reaction was removed successfully."""
        pass

    # TODO: find a way to reduce the repetition here with higher-order functions

    async def _try_reply(self, reply_content: str) -> bool:
        attempts = 0
        while attempts < self.MAX_ATTEMPTS:
            success = await self._reply(reply_content)
            if success:
                return True
            attempts += 1
        return False

    async def _try_send(self, reply_content: str) -> bool:
        attempts = 0
        while attempts < self.MAX_ATTEMPTS:
            success = await self._send(reply_content)
            if success:
                return True
            attempts += 1
        return False

    async def _try_react(self, reaction: str | None) -> bool:
        attempts = 0
        while attempts < self.MAX_ATTEMPTS:
            success = await self._react(reaction)
            if success:
                return True
            attempts += 1
        return False

    async def _try_undo_react(self, reaction: str | None) -> bool:
        attempts = 0
        while attempts < self.MAX_ATTEMPTS:
            success = await self._undo_react(reaction)
            if success:
                return True
            attempts += 1
        return False

    # NOTE: this algorithm has some room for optimization.
    # I'll take care of that eventually if it becomes a problem or bothers me too much - John
    def _split_content(self, content: str) -> tuple[str, str]:
        """Cuts off the first chunk of the content that fits within the character limit.
        This method will attempt to find a graceful place to cut the messages, but it will fall back on
        less ideal options if necessary to avoid throwing exceptions.
        Returns a tuple of (first_chunk, remaining_content)
        """
        simple_cut = content[: self.char_limit]

        def split_at(index: int) -> tuple[str, str]:
            if index == -1:
                return None
            return (content[:index].strip(), content[index + 1 :].strip())

        # First, try to split on a newline:
        split_index = simple_cut.rfind("\n")
        result = split_at(split_index)
        if result is not None:
            return result

        # Okay, let's at least try to split on a full stop then...
        split_index = last_full_stop(simple_cut)
        result = split_at(split_index)
        if result is not None:
            return result

        # Surely we can at least split on a space...
        split_index = simple_cut.rfind(" ")
        result = split_at(split_index)
        if result is not None:
            return result

        # Ok fine. We'll just chop a word in half somewhere. The model must be outputting pure nonsense...
        # _split_reply should never be called when self.char_limit == -1, so this won't return None:
        return split_at(self.char_limit)

    async def react(self, reaction: str | None = None):
        if self.disable_interactions or self.no_react:
            return False
        return await self._try_react(reaction)

    async def undo_react(self, reaction: str | None = None):
        if self.disable_interactions or self.no_react:
            return False
        return await self._try_undo_react(reaction)

    async def send(self, message_content: str) -> bool:
        if self.disable_interactions:
            return False
        if len(message_content) == 0:
            return True

        if self.char_limit == -1 or len(message_content) <= self.char_limit:
            return await self._try_send(message_content)

        (first, remaining) = self._split_content(message_content)

        while first != "":
            success = await self._try_send(first)
            if not success:
                return False
            if len(remaining) > self.char_limit:
                (first, remaining) = self._split_content(remaining)
            else:
                (first, remaining) = (remaining, "")

        return True

    async def reply(self, reply_content: str) -> bool:
        """Returns True if the reply is sent successfully.
        This method will split the reply into appropriately-sized chunks for the underlying platform.
        """
        if self.disable_interactions:
            return False

        if len(reply_content) == 0:
            return True  # Send nothing

        if self.char_limit == -1 or len(reply_content) <= self.char_limit:
            return await self._try_reply(reply_content)

        (first, remaining) = self._split_content(reply_content)

        while first != "":
            success = await self._try_reply(first)
            if not success:
                return False
            if len(remaining) > self.char_limit:
                (first, remaining) = self._split_content(remaining)
            else:
                (first, remaining) = (remaining, "")

        return True


def last_full_stop(s: str) -> int:
    """Return the last full stop in a string"""
    q_index = s.rfind("? ")
    e_index = s.rfind("! ")
    p_index = s.rfind(". ")
    index = max(q_index, e_index, p_index)
    return -1 if index == -1 else index + 1
