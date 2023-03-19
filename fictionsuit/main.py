import config
import discord
from bot import Bot
import prompts
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
   
    prefix_lower = prompts.COMMAND_PREFIX.lower()
    if not message.content.lower().startswith(prefix_lower):
        return # Not handling non-command messages, for now

    (cmd, args) = command_split(message.content, prompts.COMMAND_PREFIX)

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

# @bot.command(help = "Responds with a pong and the latency in ms")
# async def ping(ctx):
    # await bot.pingCommand(ctx)

# @bot.command(help = "Responds with the bot's current status")
# async def status(ctx):
    # pass

# @bot.command(help = "Toggles token use stats on or off")
# async def stats(ctx):
    # pass

# @bot.command(help = "Repeats a message back to the user")
# async def echo(ctx, message):
    # await ctx.send(message)

# @bot.command(help = "Prevents the bot from responding to chats until awoken")
# async def sleep(ctx):
    # pass

# @bot.command(help = "Wakes the bot from its slumber")
# async def wake(ctx):
    # pass

# @bot.command(help = "Summarizes the linked article")
# async def summarize(ctx, link):
    # pass

# @bot.command(help = "Reads the given user's twitter account and reports a vibecheck")
# async def vibecheck(ctx, user):
    # pass

# @bot.command(help = "Shifts the bot's prompt and face for that channel (note: are face-changes discord wide??)")
# async def shift(ctx, prompt):
    # pass

# @bot.command(help = "Get article and add to vector store")
# async def read(ctx, link):
    # pass

# @bot.command(help = "Remove an article from vector store (if it exists)")
# async def unread(ctx, link):
    # pass

# @bot.command(help = "Clear chat history from memory and reset to original prompt state")
# async def forget(ctx):
    # pass

# @bot.command(help = "Switch between stateless, chat history, tool use, etc")
# async def mode(ctx, mode):
    # pass

# @bot.command(help = "Show three of the likeliest completions to the prompt and let you select which one it adds to the history (selecting 1,2, or 3) , then generate three more from that one")
# async def loom(ctx):
    # pass

# @bot.command(help = "Generate a meme of the given text")
# async def meme(ctx, text):
    # pass

