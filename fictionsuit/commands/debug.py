import time

import tiktoken

from .. import config
from ..core.user_message import UserMessage
from .command_group import CommandGroup


class Debug(CommandGroup):
    async def cmd_ping(self, message: UserMessage, args: str) -> str:
        """Returns the one-way latency from the user to the bot.
        Usage:
        `ping`"""
        timestamp = await message.get_timestamp()
        now = time.time()
        latency = round(now - timestamp)
        response = f"Pong! Latency {latency} ms"
        return response

    async def cmd_react(self, message: UserMessage, args: str) -> None:
        """Reacts to the message.
        Usage:
        `react`
        `react {emoji}`"""
        await message.react()

    # TODO: a more graceful cmd_exit would be nice - one that shuts the process down in a more controlled manner
    async def cmd_kill(self, message: UserMessage, args: str) -> None:
        """Immediately and unceremoniously kills the entire python process.
        Usage:
        `kill`"""
        exit()

    async def cmd_tokens(self, message: UserMessage, args: str) -> int:
        """Returns the number of tokens in the `cl100k_base` tiktoken encoding of the given text.
        Usage:
        `tokens {text}`"""
        try:
            encoding = tiktoken.encoding_for_model(config.OAI_MODEL)
        except KeyError:
            encoding = tiktoken.get_encoding("cl100k_base")
        num_tokens = len(encoding.encode(args))
        await message.reply(f"Number of tokens in text: {num_tokens}")
        return num_tokens
