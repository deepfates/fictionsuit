import config
import discord
from bot import Bot
from commands.basics import Basics

intents = discord.Intents.default()
intents.message_content = True

bot = Bot(intents=intents)

@bot.event
async def on_message(message):
    if message.author == bot.user:
        # Don't self-reply
        return
    
    for group in command_groups:
        if await group.handle(message):
            return
    

def main():
    global command_groups
    command_groups = [Basics()]

    if config.SERVER == "dev":
        bot.run(config.DEV_TOKEN)
    elif config.SERVER == "prod":
        bot.run(config.PROD_TOKEN)

if __name__ == '__main__':
    main()

