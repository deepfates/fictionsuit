from .command_group import CommandGroup
from ..api_wrap.user_message import UserMessage
from ..core.core import chat_message, get_openai_response
from ..utils import make_stats_str

from .. import config

class Chat(CommandGroup):
    async def cmd_chat(self, message: UserMessage, args: str) -> str:
        messages = chat_message('system', config.SYSTEM_MSG)
        messages += chat_message('user', args)
        res = await get_openai_response(messages)
        content = res['choices'][0]['message']['content']
        await message.reply(content)
        return content
