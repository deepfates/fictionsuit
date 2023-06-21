import discord

from fictionsuit.api_wrap import DiscordBotClient
from fictionsuit.commands import Methods, Debug, DiscordOnly, Research, Text
from fictionsuit.commands.mpt import MPT
from fictionsuit.core import BasicCommandSystem


def main():
    intents = discord.Intents.default()
    intents.message_content = True
    intents.members = True

    command_groups = [Debug(), Research(), Methods(), Text(), DiscordOnly(), MPT()]

    system = BasicCommandSystem(
        command_groups,
        respond_on_unrecognized=True,
        stats_ui=False,
        enable_scripting=True,
    )

    client = DiscordBotClient(system, intents=intents)

    client.run()


if __name__ == "__main__":
    main()
