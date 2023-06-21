from ..core.user_message import UserMessage
from .command_group import CommandGroup


class WebUi(CommandGroup):
    """Commands for the web UI."""

    async def cmd_motd(self, message: UserMessage, args: str):
        """Show a message to a user who has just begun a new session."""
        return "Welcome to FictionScript! The `help` command can be used to retrieve the documentation of any command.\n\nFor a list of all available commands, try `cmds`.\n\nFor LLM-enhanced help, use `<help>`."
