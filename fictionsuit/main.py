import config
import discord
from bot import Bot
import prompts

intents = discord.Intents.default()
intents.message_content = True

bot = Bot(intents=intents)

# Commands: 
# help displays the list of commands and how to use them, plus misc info
# status displays the bot's current status e.g. whether it is slept in the channel
# stats turns token use stats on or off
# ping responds with "pong!" and the latency
# echo repeats a message back to the user
# sleep prevents the bot from responding to chats until awoken
# wake wakes the bot from its slumber
# summarize summarizes the linked article
# vibecheck Reads the given user's twitter account and reports a vibecheck
# shift shifts the bot's prompt and face for that channel (note: are face-changes discord wide??)
# read get article and add to vector store
# unread remove an article from vector store (if it exists)
# forget clear chat history from memory and reset to original prompt state
# mode switch between stateless, chat history, tool use, etc
# loom show three of the likeliest completions to the prompt and let you select which one it adds to the history (selecting 1,2, or 3) , then generate three more from that one
# meme generate a meme of the given text

@bot.command(help = "Responds with a pong and the latency in ms")
async def ping(ctx):
    await bot.pingCommand(ctx)

@bot.command(help = "Responds with the bot's current status")
async def status(ctx):
    pass

@bot.command(help = "Toggles token use stats on or off")
async def stats(ctx):
    pass

@bot.command(help = "Repeats a message back to the user")
async def echo(ctx, message):
    await ctx.send(message)

@bot.command(help = "Prevents the bot from responding to chats until awoken")
async def sleep(ctx):
    pass

@bot.command(help = "Wakes the bot from its slumber")
async def wake(ctx):
    pass

@bot.command(help = "Summarizes the linked article")
async def summarize(ctx, link):
    pass

@bot.command(help = "Reads the given user's twitter account and reports a vibecheck")
async def vibecheck(ctx, user):
    pass

@bot.command(help = "Shifts the bot's prompt and face for that channel (note: are face-changes discord wide??)")
async def shift(ctx, prompt):
    pass

@bot.command(help = "Get article and add to vector store")
async def read(ctx, link):
    pass

@bot.command(help = "Remove an article from vector store (if it exists)")
async def unread(ctx, link):
    pass

@bot.command(help = "Clear chat history from memory and reset to original prompt state")
async def forget(ctx):
    pass

@bot.command(help = "Switch between stateless, chat history, tool use, etc")
async def mode(ctx, mode):
    pass

@bot.command(help = "Show three of the likeliest completions to the prompt and let you select which one it adds to the history (selecting 1,2, or 3) , then generate three more from that one")
async def loom(ctx):
    pass

@bot.command(help = "Generate a meme of the given text")
async def meme(ctx, text):
    pass

if config.SERVER == "dev":
    bot.run(config.DEV_TOKEN)
elif config.SERVER == "prod":
    bot.run(config.PROD_TOKEN)
