from typing import Sequence

from ..commands.failure import CommandFailure

from .. import config
from ..api_wrap.openai import ChatInstance
from ..commands.command_group import (
    CommandGroup,
    CommandHandled,
    CommandNotFound,
    PartialReply,
    command_split,
)
from ..commands.scripting import Scripting
from ..utils import make_stats_str
from .system import System
from .user_message import UserMessage


class BasicCommandSystem(System):
    def __init__(
        self,
        command_groups: Sequence[CommandGroup],
        stats_ui: bool = True,
        respond_on_unrecognized: bool = False,
        enable_scripting: bool = False,
    ):
        self.command_groups = command_groups
        self.stats_ui = stats_ui
        self.respond_on_unrecognized = respond_on_unrecognized

        all_commands = [
            command for group in command_groups for command in group.get_command_names()
        ]

        # TODO: this doesn't actually work; figure out why
        if len(all_commands) != len(set(all_commands)):
            # TODO: Print out more useful information, like where the name collision actually is.
            print(
                f'{"!"*20}\n\nWARNING: MULTIPLE COMMANDS WITH OVERLAPPING COMMAND NAMES\n\n{"!"*20}'
            )

        self.slow_commands = None
        self.scripting_group = None

        if enable_scripting:
            self.scripting_group = Scripting(self.command_groups)
            self.command_groups += [self.scripting_group]

        for group in self.command_groups:
            group.system = self
            group.inspect_other_groups(self.command_groups)

        self.message_history = []

    async def enqueue_message(
        self,
        message: UserMessage,
        return_failures: bool = False,
        return_returns: bool = False,
        return_whatever: bool = False,
    ):
        content = message.content

        if return_whatever:
            return_failures = True
            return_returns = True

        try:
            for group in self.command_groups:
                content = await group.intercept_content(content)
                if isinstance(content, CommandFailure):
                    if return_failures:
                        return content
                    await message.reply(
                        f"Failed in content interceptor of command group {group.__class__.__name__}:\n{content}"
                    )
                    return
        except Exception as e:
            await message.reply(f"Content interceptor threw an exception: {e}")
            content = message.content

        if content.startswith("#"):
            return  # Comment.

        (cmd, args) = command_split(content)

        if cmd is None:
            return  # Nothing to do.

        if self.slow_commands is None:
            self.slow_commands = []
            for group in self.command_groups:
                self.slow_commands += group.get_slow_commands()

        cmd_is_slow = cmd in self.slow_commands

        if cmd_is_slow:
            await message.react("⏳")

        accumulator = None

        for group in self.command_groups:
            if accumulator is not None:
                result = await group.handle(message, cmd, args, accumulator)
            else:
                result = await group.handle(message, cmd, args)
            if not isinstance(result, CommandNotFound):
                self.last = result
                if isinstance(result, CommandFailure):
                    if cmd_is_slow:
                        await message.undo_react("⏳")
                    await message.react("❌")
                    await message.reply(f'Command "{cmd}" failed:\n{result}')
                    return result if return_failures else None
                if return_returns and cmd == "return":
                    return result
                if isinstance(result, PartialReply):
                    accumulator = result
                    continue
                if return_whatever:
                    return result
                if isinstance(result, CommandHandled):
                    if cmd_is_slow:
                        await message.undo_react("⏳")
                    await message.react("✅")
                    return
                if self.scripting_group is not None and hasattr(result, "name"):
                    if result.name is None or result.name == "":
                        result.name = "anon"
                    self.scripting_group.vars[result.name] = result
                try:
                    result = str(result)
                except ValueError:
                    pass
                if cmd_is_slow:
                    await message.undo_react("⏳")
                await message.reply(result)
                return

        if accumulator is not None:
            if cmd_is_slow:
                await message.undo_react("⏳")
            await message.reply(accumulator)
            if return_whatever:
                return accumulator
            return

        await message.undo_react("⏳")

        if self.respond_on_unrecognized:
            await self.direct_chat(message)
        else:
            if return_failures:
                return CommandFailure(f'Command "{cmd}" not recognized.')
            else:
                await message.reply(f'Command "{cmd}" not recognized.')

    async def direct_chat(self, message: UserMessage):
        if hasattr(message, "discord_message"):
            await message.discord_message.channel.typing()
        chat = ChatInstance()
        await chat.system(config.SYSTEM_MSG)
        await chat.user(message.content)
        content = await chat.continue_()
        content = (
            make_stats_str(content, chat.history, "chat") if self.stats_ui else content
        )
        await message.undo_react("⏳")
        await message.reply(content)

    # Retrieve history of the chat and return list of UserMessages
    async def retrieve_history(channel_id):
        messages = []
