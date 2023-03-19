import config
import discord
from bot import Bot
import time

from commands.command_group import command_split
from commands.basics import Basics

intents = discord.Intents.default()
intents.message_content = True

bot = Bot(intents=intents)

@bot.event
async def on_message(message):
    if message.author == bot.user:
        # Don't self-reply
        return
   
    prefix_lower = config.COMMAND_PREFIX.lower()
    if not message.content.lower().startswith(prefix_lower):
        return # Not handling non-command messages, for now

    (cmd, args) = command_split(message.content, config.COMMAND_PREFIX)

    if cmd is None:
        return # Prefix, but no command. Nothing to do.

    for group in command_groups:
        if await group.handle(message, cmd, args):
            return

    if cmd == 'help':
        await message.channel.send(f'Sorry, there\'s no command called "{args}"')
    

def main():
    global command_groups
    command_groups = [Basics()]

    all_commands = [command for group in command_groups for command in group.get_all_commands()]

    if len(all_commands) != len(set(all_commands)):
        # TODO: Print out more useful information, like where the name collision actually is.
        print(f'{"!"*20}\n\nWARNING: MULTIPLE COMMANDS WITH OVERLAPPING COMMAND NAMES\n\n{"!"*20}')

    if config.SERVER == "dev":
        bot.run(config.DEV_TOKEN)
    elif config.SERVER == "prod":
        bot.run(config.PROD_TOKEN)

if __name__ == '__main__':
    main()

