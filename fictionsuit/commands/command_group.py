from __future__ import annotations

import string
import traceback
from typing import Any, Callable

from ..core.user_message import UserMessage

# TODO: this file is doing way too many things. probably best to extract to a module


class CommandNotFound:
    pass


class CommandHandled:
    pass


class CommandFailure(str):
    def __new__(cls, *args, **kwargs):
        return str.__new__(cls, *args, **kwargs)


class CommandReply(str):
    def __new__(cls, *args, **kwargs):
        return str.__new__(cls, *args, **kwargs)


class PartialReply(str):
    def __new__(cls, *args, **kwargs):
        return str.__new__(cls, *args, **kwargs)


CommandResult = Any | None


def slow_command(command):
    command.is_slow = True
    return command


def auto_reply(command):
    """Wraps a command the returns `str | None`, causing the command to reply automatically with the returned string."""

    async def _command(s, m, a):
        result = await command(s, m, a)
        return CommandReply(result) if type(result) is str else result

    _command.__doc__ = command.__doc__
    _command.__name__ = command.__name__
    return _command


def default_on_none(default):
    def _default_on_none(command):
        async def _command(s, m, a, r):
            result = await command(s, m, a, r)
            return default if result is None else result

        if hasattr(command, "multi_command"):
            _command.multi_command = True
        _command.__doc__ = command.__doc__
        _command.__name__ = command.__name__
        return _command

    return _default_on_none


def multi_command(combiner: Callable[[str, str | None], str]):
    def _multi_command(command):
        async def _command(
            self, msg: UserMessage, args: str, result: PartialReply | None
        ) -> PartialReply | None:
            next_result = await command(self, msg, args)
            next_result = PartialReply(next_result) if next_result is not None else None
            return (
                next_result
                if result is None
                else PartialReply(combiner(result, next_result))
            )

        _command.multi_command = True
        _command.__doc__ = command.__doc__
        _command.__name__ = command.__name__
        return _command

    return _multi_command


class CommandGroup:
    """Extend this class to create a group of command handlers for the bot.
    A handler consists of: a function whose name starts with "cmd_" that accepts the arguments (self, message, args)

    The rest of the function name is the command name.
    "message" is the UserMessage that contains the command
    "args" is everything in the message after the command prefix and command name
    A handler's name must not contain any upper-case characters. Usage will not be case-sensitive.
    """

    async def handle(
        self,
        message: UserMessage,
        command: str,
        args: str,
        accumulator: PartialReply | None = None,
    ) -> CommandResult:
        """Attempt to handle the command."""
        try:
            cmd_handler = f"cmd_{command}".lower()
            if not hasattr(self, cmd_handler):
                # No handler
                return CommandNotFound()

            handler = getattr(self, cmd_handler)

            if accumulator is None and not hasattr(handler, "multi_command"):
                handler_result = await handler(message, args)
            else:
                handler_result = await handler(message, args, accumulator)

            if handler_result is None and not hasattr(handler, "multi_command"):
                handler_result = CommandHandled()

            return handler_result
        except Exception as e:
            err_msg = f"Exception thrown by {command} handler: {e}\n```{traceback.format_exc()}```"
            return CommandFailure(err_msg)

    def inspect_other_groups(self, groups: list[CommandGroup]):
        pass

    async def intercept_content(self, content: str) -> str:
        """Intercept and modify the content of an incoming UserMessage."""
        return content

    @default_on_none(PartialReply(""))
    @multi_command(
        lambda x, y: PartialReply("\n\n".join((x, y))) if y is not None else x
    )
    async def cmd_cmds(self, message: UserMessage, args: str) -> str | None:
        """`cmds` - print out a list of all available commands"""
        response = f"**__{self.__class__.__name__}__**\n  > "
        response += "\n  > ".join(self.get_all_commands())
        return response

    @default_on_none(PartialReply(""))
    @multi_command(
        lambda x, y: PartialReply("\n\n".join((x, y)).strip()) if y is not None else x
    )
    async def cmd_help(self, message: UserMessage, args: str) -> str | None:
        """`help {cmd}` - print the help for command `cmd`
        `help` - with no command, acts as an alias for `cmds`"""
        if args == "":
            response = f"**__{self.__class__.__name__}__**\n  > "
            response += "\n  > ".join(self.get_all_commands())
            return response

        command = args.split(maxsplit=1)[0]

        response = None

        command_handler_name = f"cmd_{command}".lower()

        if hasattr(self, command_handler_name):
            handler = getattr(self, command_handler_name)
            if handler.__doc__ is not None:
                name = string.capwords(handler.__name__[4:].replace("_", " "))
                response = f"**__{name}__**\n{handler.__doc__}"
            else:
                response = f'Sorry, the "{command}" command is missing documentation.'

        if response is None:
            return

        return response

    def get_slow_commands(self) -> list[str]:
        cmds = [x for x in self.__class__.__dict__ if x.startswith("cmd_")]
        return [x[4:] for x in cmds if hasattr(self.__class__.__dict__[x], "is_slow")]

    def get_all_commands(self) -> list[str]:
        return [x[4:] for x in self.__class__.__dict__ if x.startswith("cmd_")]


# TODO: Unit testing
def command_split(content: str, prefix: str) -> tuple[str, str]:
    """given a string that starts with the command prefix,
    returns the command and its arguments as a tuple.

    If there is no command, the command will be None
    If there are no arguments, the arguments will be an empty string.

    **It is the caller's responsibility to ensure that the string starts with the prefix.**
    """
    after_prefix = content[len(prefix) :].strip()

    if after_prefix == "":
        return (None, "")  # No command

    split_content = after_prefix.split(maxsplit=1)

    cmd = split_content[0]

    if len(split_content) == 1:  # No args
        args = ""
    else:
        args = split_content[1]

    return (cmd, args)
