import re

from .failure import CommandFailure

from ..core.user_message import UserMessage
from .command_group import CommandGroup


class Text(CommandGroup):
    """Text manipulation & interpretation helper methods."""

    _cleaner = re.compile("[^a-zA-Z]")

    async def cmd_reverse(
        self, message: UserMessage, args: str
    ) -> str | CommandFailure:
        """Reverse the order of the characters in the given text.
        Usage:
        `reverse {text}`"""
        return args[::-1]

    # Tetralemma
    def _which(self, a: str, b: str, text: str) -> tuple[bool, str]:
        low = Text._cleaner.sub(" ", text.lower()).split()
        is_a = a.lower() in low
        is_b = b.lower() in low
        if is_a and not is_b:
            return (True, a)
        if is_b and not is_a:
            return (True, b)
        if is_a:  # both
            return (False, "both")
        # neither
        return (False, "neither")

    def _is_x(self, a: str, b: str, x: str, text: str) -> bool:
        (classical, result) = self._which(a, b, text)
        return result == x if classical else result == "both"

    def _is_not_x(self, a: str, b: str, x: str, text: str) -> bool:
        (classical, result) = self._which(a, b, text)
        return result != x if classical else result == "neither"

    def _is_just_x(self, a: str, b: str, x: str, text: str) -> bool:
        (classical, result) = self._which(a, b, text)
        return result == x if classical else False

    def _is_not_just_x(self, a: str, b: str, x: str, text: str) -> bool:
        (classical, result) = self._which(a, b, text)
        return result != x if classical else True

    # One must be careful when trying to extract classical truth values from the answers of a language model

    async def cmd_is_true(self, message: UserMessage, args: str) -> bool:
        return self._is_x("true", "false", "true", args)

    async def cmd_just_true(self, message: UserMessage, args: str) -> bool:
        return self._is_just_x("true", "false", "true", args)

    async def cmd_is_false(self, message: UserMessage, args: str) -> bool:
        return self._is_x("true", "false", "false", args)

    async def cmd_just_false(self, message: UserMessage, args: str) -> bool:
        return self._is_just_x("true", "false", "false", args)

    async def cmd_not_true(self, message: UserMessage, args: str) -> bool:
        return self._is_not_x("true", "false", "true", args)

    async def cmd_not_just_true(self, message: UserMessage, args: str) -> bool:
        return self._is_not_just_x("true", "false", "true", args)

    async def cmd_not_false(self, message: UserMessage, args: str) -> bool:
        return self._is_not_x("true", "false", "false", args)

    async def cmd_not_just_false(self, message: UserMessage, args: str) -> bool:
        return self._is_not_just_x("true", "false", "false", args)

    # When you just want a simple "yes" or "no"...

    async def cmd_is_yes(self, message: UserMessage, args: str) -> bool:
        return self._is_x("yes", "no", "yes", args)

    async def cmd_just_yes(self, message: UserMessage, args: str) -> bool:
        return self._is_just_x("yes", "no", "yes", args)

    async def cmd_is_no(self, message: UserMessage, args: str) -> bool:
        return self._is_x("yes", "no", "no", args)

    async def cmd_just_no(self, message: UserMessage, args: str) -> bool:
        return self._is_just_x("yes", "no", "no", args)

    async def cmd_not_yes(self, message: UserMessage, args: str) -> bool:
        return self._is_not_x("yes", "no", "yes", args)

    async def cmd_not_just_yes(self, message: UserMessage, args: str) -> bool:
        return self._is_not_just_x("yes", "no", "yes", args)

    async def cmd_not_no(self, message: UserMessage, args: str) -> bool:
        return self._is_not_x("yes", "no", "no", args)

    async def cmd_not_just_no(self, message: UserMessage, args: str) -> bool:
        return self._is_not_just_x("yes", "no", "no", args)
