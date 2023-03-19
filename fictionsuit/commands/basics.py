import time
from commands.command_group import CommandGroup

class Basics(CommandGroup):
    async def cmd_ping(self, message, args):
        timestamp = message.created_at.timestamp()
        now = time.time()
        latency = round(now - timestamp)
        response = f"Pong! Latency {latency} ms"
        await message.channel.send(response)

