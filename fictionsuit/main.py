import config
import discord
from bot import Bot
import prompts

intents = discord.Intents.default()
intents.message_content = True

bot = Bot(intents=intents)

@bot.command(help = "Responds with a pong and the latency in ms")
async def ping(ctx):
    await bot.pingCommand(ctx)



if config.SERVER == "dev":
    bot.run(config.DEV_TOKEN)
elif config.SERVER == "prod":
    bot.run(config.PROD_TOKEN)
