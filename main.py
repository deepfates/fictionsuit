import config
import discord
from bot import Bot

intents = discord.Intents.default()
intents.typing = True
intents.message_content = True
intents.presences = True
client = discord.Client(intents=intents)

bot = Bot()


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith(bot.command_prefix):
        res = bot.respond(message.content)
        await message.channel.send(res)


if config.SERVER == "dev":
    client.run(config.DEV_TOKEN)
elif config.SERVER == "prod":
    client.run(config.PROD_TOKEN)
