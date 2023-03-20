import openai
import config
from utils import make_stats_str
from discord.ext import commands
import time
import discord
from core import get_openai_response


class Bot(commands.Bot):
    def __init__(
        self,
        system_msg=config.SYSTEM_MSG,
        stats_ui=True,
        command_prefix=config.COMMAND_PREFIX,
        mode="chat",
        intents=discord.Intents.default()
    ):
        super().__init__(command_prefix=command_prefix, intents=intents) #TODO: move intents to main.py
        self.system_msg = system_msg
        self.messages = [{"role": "system", "content": system_msg}]
        self.stats_ui = stats_ui
        self.command_prefix = command_prefix
        self.mode = mode

    def toggle_stats_ui(self, content, messages):
        if self.stats_ui:
            str = make_stats_str(content, messages, self.mode)
            return str
        else:
            return content
        
    def respond(self, message):  # main entryway for bot
        res = get_openai_response(messages_list=[{"role": "system", "content": config.SYSTEM_MSG}, {"role": "user", "content": message}])
        content = res["choices"][0]["message"]["content"]
        return self.toggle_stats_ui(content, self.messages)
