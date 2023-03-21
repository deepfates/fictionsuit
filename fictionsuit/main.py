import discord

import config
from commands.debug import Debug
from commands.research import Research
from api_wrap.discord import DiscordBotClient
from core import BasicCommandSystem

def main():
    intents = discord.Intents.default()
    intents.message_content = True
    intents.members = True

    command_groups = [
        Debug(),
        Research()
            ]

    system = BasicCommandSystem(command_groups, respond_on_unrecognized=True, stats_ui=False)

    client = DiscordBotClient(system, intents=intents)

    client.run()

if __name__ == '__main__':
    main()


