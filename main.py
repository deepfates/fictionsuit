import discord
import asyncio
from fictionsuit.commands.debug import Debug
from fictionsuit.commands.research import Research
from fictionsuit.api_wrap.discord import DiscordBotClient
from fictionsuit.core.basic_command_system import BasicCommandSystem
from fictionsuit.db.supa import build_annoy_index


def main():
    intents = discord.Intents.default()
    intents.message_content = True
    intents.members = True
    # Use asyncio.run() to run the async function build_annoy_index()
    annoy_index, id_mapping, id_mapping_chunk = asyncio.run(build_annoy_index())
    command_groups = [
        Debug(),
        Research(annoy_index, id_mapping, id_mapping_chunk),
    ]

    system = BasicCommandSystem(
        command_groups, respond_on_unrecognized=True, stats_ui=False
    )

    client = DiscordBotClient(system, intents=intents)

    client.run()


if __name__ == "__main__":
    main()
