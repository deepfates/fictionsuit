import discord

from fictionsuit.commands.debug import Debug
from fictionsuit.commands.research import Research
from fictionsuit.api_wrap.discord import DiscordBotClient
from fictionsuit.core.basic_command_system import BasicCommandSystem


def main():
    intents = discord.Intents.default()
    intents.message_content = True
    intents.members = True

    command_groups = [Debug(), Research()]

    system = BasicCommandSystem(
        command_groups, respond_on_unrecognized=True, stats_ui=False
    )

    client = DiscordBotClient(system, intents=intents)

    client.run()


if __name__ == "__main__":
    main()
