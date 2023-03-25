from .. import config
from ..api_wrap import UserMessage
from ..core import chat_message, get_openai_response
from .command_group import CommandGroup, auto_reply, slow_command


class Chat(CommandGroup):
    @slow_command
    @auto_reply
    async def cmd_chat(self, message: UserMessage, args: str) -> str:
        """Sends the arguments as a user message to a fresh ChatGPT instance,
        with nothing but the environment-defined system message (config.SYSTEM_MSG) preceding it.
        """
        messages = chat_message("system", config.SYSTEM_MSG)
        messages += chat_message("user", args)
        res = await get_openai_response(messages)
        content = res["choices"][0]["message"]["content"]
        return content
