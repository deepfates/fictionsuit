import time
from commands.command_group import CommandGroup
from utils import send_long_message
from chains import reply_chain
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
        response = "This command is not yet implemented. Sorry!"
        await send_long_message(message.channel, response)

    async def cmd_reply(self, message, args):
        """**__Reply__**
        `prefix reply` - returns a response to rest of the message
        """
        response = await reply_chain.arun(args)
        await send_long_message(message.channel, response)