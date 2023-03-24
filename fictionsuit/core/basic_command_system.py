from ..commands.meta import Meta
from ..utils import make_stats_str
from .. import config
from typing import Callable, Sequence
from ..api_wrap.user_message import UserMessage
from ..commands.command_group import (
    CommandFailure,
    CommandGroup,
    CommandNotFound,
    CommandNotHandled,
    command_split,
)
from .core import chat_message, get_openai_response
from ..api_wrap.discord import DiscordMessage
from .system import System


class BasicCommandSystem(System):
    def __init__(
        self,
        command_groups: Sequence[CommandGroup],
        stats_ui: bool = True,
        respond_on_unrecognized: bool = False,
    ):
        self.command_groups = command_groups
        self.stats_ui = stats_ui
        self.respond_on_unrecognized = respond_on_unrecognized

        all_commands = [
            command for group in command_groups for command in group.get_all_commands()
        ]

        if len(all_commands) != len(set(all_commands)):
            # TODO: Print out more useful information, like where the name collision actually is.
            print(
                f'{"!"*20}\n\nWARNING: MULTIPLE COMMANDS WITH OVERLAPPING COMMAND NAMES\n\n{"!"*20}'
            )

    def add_meta_group(self):
        self.command_groups += [Meta(self, self.command_groups)]

    async def enqueue_message(
        self, message: UserMessage, return_failures: bool = False
    ):
        content = message.content

        try:
            for group in self.command_groups:
                content = await group.intercept_content(content)
        except Exception as e:
            await message.reply(f"Error in content interception: {e}")
            content = message.content

        if not message.has_prefix(config.COMMAND_PREFIX):
            return  # Not handling non-command messages, for now

        (cmd, args) = command_split(content, config.COMMAND_PREFIX)

        if cmd is None:
            return  # Nothing but a prefix. Nothing to do.

        for group in self.command_groups:
            result = await group.handle(message, cmd, args)
            if type(result) is not CommandNotFound:
                if type(result) is CommandFailure:
                    await message.reply(f'Command "{cmd}" failed.\n{result.message}')
                    if return_failures:
                        return result
                if type(result) is not CommandNotHandled:
                    return

        if cmd == "help":
            await message.reply(f'Sorry, there\'s no command called "{args}".')
            return

        if self.respond_on_unrecognized:
            await self.direct_chat(message)

    async def direct_chat(self, message: UserMessage):
        if isinstance(message, DiscordMessage):
            await message.discord_message.channel.typing()
        messages = []
        # messages = await message.retrieve_history()
        messages += chat_message("system", config.SYSTEM_MSG)
        messages += chat_message("user", message.content)
        res = await get_openai_response(messages)
        content = res["choices"][0]["message"]["content"]
        content = (
            make_stats_str(content, messages, "chat") if self.stats_ui else content
        )
        await message.reply(content)

    # Retrieve history of the chat and return list of UserMessages
    async def retrieve_history(channel_id):
        messages = []