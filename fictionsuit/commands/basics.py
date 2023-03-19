import time
from commands.command_group import CommandGroup
from utils import send_long_message
from utils import read_url
from core import summarize

class Basics(CommandGroup):
    async def cmd_ping(self, message, args):
        """**__Ping__**
        `prefix ping` - returns the one-way latency from the user to the bot
        """
        timestamp = message.created_at.timestamp()
        now = time.time()
        latency = round(now - timestamp)
        response = f"Pong! Latency {latency} ms"
        await message.channel.send(response)

    async def cmd_summarize(self, message, args):
        """**__Summarize__**
        `prefix summarize` - returns a summary of the linked article
        """
        # Find urls in message
        url = args
        print(url)
        text = read_url(url)
        # Summarize the text
        summary = await summarize(text)
        # Send the summary
        await send_long_message(message.channal, summary)

