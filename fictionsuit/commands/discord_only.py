from .failure import CommandFailure
from ..core.user_message import UserMessage
from .command_group import CommandGroup


class DiscordOnly(CommandGroup):
    """Commands that are only available in the Discord server."""

    async def cmd_discord_nickname(self, message: UserMessage, args: str):
        """Set the bot's nickname in the current server.
        Usage:
        `discord_nickname {nickname}`"""
        if not hasattr(message, "set_nickname"):
            return CommandFailure("This command is only available on Discord.")
        try:
            await message.set_nickname(args)
        except Exception as e:
            return CommandFailure(f"Failed to set nickname: {e}")
