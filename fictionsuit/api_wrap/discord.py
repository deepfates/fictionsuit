import discord
from discord import Message
from discord.ext import commands

from .. import config
from ..core.system import System
from ..core.user_message import UserMessage
from .openai import ApiMessages, api_message


class DiscordBotClient(commands.Bot):
    def __init__(
        self,
        system: System,
        system_msg=config.SYSTEM_MSG,
        command_prefix=config.COMMAND_PREFIX,
        mode="chat",
        intents=discord.Intents.default(),
    ):
        super().__init__(
            command_prefix=command_prefix, intents=intents
        )  # TODO: move intents to main.py
        self.system = system
        self.system_msg = system_msg
        self.messages = [{"role": "system", "content": system_msg}]
        self.command_prefix = command_prefix
        self.mode = mode
        self.as_member_of = {}

    async def on_guild_join(self, server):
        self.as_member_of[server.id] = await self.get_self_as_member(server)

    async def on_message(self, message: Message):
        if message.author == self.user:
            # Don't self-reply
            return

        content = message.content.lstrip()

        if not content.lower().startswith(self.command_prefix.lower()):
            return

        message.content = content[len(self.command_prefix) :].lstrip()

        wrap = DiscordMessage(self, message)
        await self.system.enqueue_message(wrap)

    def run(self):
        if config.SERVER == "dev":
            super().run(config.DEV_TOKEN)
        else:
            super().run(config.PROD_TOKEN)

    # There's gotta be a better way to do this
    async def get_self_as_member(self, server):
        # TODO: Make this work for servers with more than 100 members
        async for member in server.fetch_members(limit=100):
            if member == self.user:
                return member
        raise Exception("Anattā")

    async def set_nickname(self, server, nickname):
        botMember = await self.get_self_as_member(server)
        await botMember.edit(nick=nickname)


class DiscordMessage(UserMessage):
    """Wraps a discord message for platform-agnostic use."""

    def __init__(self, client: DiscordBotClient, message: Message):
        self.discord_message = message
        super().__init__(message.content, message.author.name)
        self.char_limit = 2000
        self.client = client

    async def set_nickname(self, nickname: str):
        await self.client.set_nickname(self.discord_message.guild, nickname)

    async def _send(self, message_content: str) -> bool:
        try:
            result = await self.discord_message.channel.send(message_content)
            return result is not None
        except Exception as e:
            print(f"Exception in discord message send: {e}")
            return False

    async def _react(self, reaction: str | None) -> bool:
        if reaction is None:
            reaction = "👍"
        try:
            result = await self.discord_message.add_reaction(reaction)
            return result is not None
        except Exception as e:
            print(f"Exception in discord reaction: {e}")
            return False

    async def _undo_react(self, reaction: str | None) -> bool:
        if reaction is None:
            reaction = "👍"
        try:
            server = self.discord_message.guild
            if server.id not in self.client.as_member_of:
                self.client.as_member_of[
                    server.id
                ] = await self.client.get_self_as_member(server)
            self_member = self.client.as_member_of[self.discord_message.guild.id]
            result = await self.discord_message.remove_reaction(reaction, self_member)
            return result is not None
        except Exception as e:
            print(f"Exception in discord reaction removal: {e}")
            return False

    async def _reply(self, reply_content: str) -> bool:
        try:
            result = await self.discord_message.reply(reply_content)
            return result is not None
        except Exception as e:
            print(f"Exception in discord message send: {e}")
            return False

    async def _retrieve_history(
        self,
        limit: int = 10,
    ) -> ApiMessages:
        messages = []
        history = self.discord_message.channel.history(
            before=self.discord_message, limit=limit
        )
        async for msg in history:
            if msg.author == self.client.user:
                role = "assistant"
                content = msg.content
            else:
                role = "user"
                content = f"{msg.author.name}: " + msg.content

            messages += api_message(role, content)

        messages.reverse()

        return messages

    async def _get_timestamp(self) -> float:
        return self.discord_message.created_at.timestamp()
