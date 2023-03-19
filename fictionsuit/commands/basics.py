import time
from commands.command_group import CommandGroup
from core import summarize
import config
import tiktoken

class Basics(CommandGroup):
    async def cmd_ping(self, message, args):
        """**__Ping__**
        `prefix ping` - returns the one-way latency from the user to the bot
        """
        timestamp = await message.get_timestamp()
        now = time.time()
        latency = round(now - timestamp)
        response = f"Pong! Latency {latency} ms"
        await message.reply(response)

    async def cmd_lorem(self, message, args):
        """**__Lorem Ipsum__**
        `prefix lorem` - returns a few paragraphs of lorem ipsum
        """
        await message.reply("""
        Lorem ipsum dolor sit amet, consectetur adipiscing elit. Ut faucibus nibh quam, non interdum mi egestas id. Nam dapibus mattis metus, sed lacinia risus eleifend ac. Suspendisse et neque orci. Nulla molestie a magna ac gravida. Ut commodo ut est eleifend suscipit. Proin varius interdum nulla sit amet imperdiet. Suspendisse id ultricies urna. Nulla facilisi. Vivamus luctus ac nisl vitae rhoncus. Vivamus in pulvinar est. Donec dictum faucibus interdum.

Vivamus vitae nibh arcu. Donec massa dolor, posuere a auctor id, ultricies ut turpis. Etiam placerat sem eu consectetur consectetur. Donec consequat, nunc ut maximus dignissim, eros orci dictum magna, at placerat ligula ipsum a nisl. In sit amet vestibulum eros, rutrum pulvinar est. Nullam iaculis velit quis nulla lacinia, eu hendrerit lectus commodo. Maecenas ut imperdiet nisi, at bibendum leo.

Praesent non fermentum metus. Sed vulputate metus id nulla vestibulum luctus. Nam vitae augue erat. Duis vestibulum, erat dignissim malesuada malesuada, nisl nisl egestas neque, sed eleifend dui urna in eros. Fusce efficitur porta condimentum. Suspendisse tincidunt magna sagittis pretium pharetra. Vestibulum sodales, metus id porta elementum, velit quam malesuada nisi, vitae varius metus felis sit amet tellus. Duis vel pulvinar magna. Duis non iaculis magna, tempor ultrices neque. Cras odio urna, hendrerit sed sodales a, pharetra sed purus.

Morbi lobortis lorem est, et commodo nisl blandit quis. Fusce vel velit et arcu fringilla fringilla pulvinar eget nisl. Quisque viverra sagittis ex, sit amet malesuada odio finibus sed. Sed commodo consectetur mi convallis scelerisque. Suspendisse iaculis libero vitae augue porttitor, vel mollis dui facilisis. Nulla et suscipit urna. Phasellus commodo rutrum magna, quis ultricies purus posuere sit amet.

Vivamus porta in mi hendrerit consequat. Integer blandit placerat dui ut porta. Sed congue dolor leo, vel interdum ante posuere non. Proin dignissim vitae ligula vel interdum. Aliquam at nunc non felis dapibus placerat. Aliquam id tempus sapien. Morbi tempor luctus mauris sed consectetur. Etiam sagittis pharetra pellentesque.
        """)


    async def cmd_summarize(self, message, args):
        """**__Summarize__**
        `prefix summarize` - returns a summary of the linked article
        """
        summary = await summarize(args)
        await message.reply(summary) 


    async def cmd_tokens(self , message, args):
        """**__Tokens__**
        `prefix tokens` - returns the number of tokens in the given text
        """
        try:
            encoding = tiktoken.encoding_for_model(config.OAI_MODEL)    
        except KeyError:
            encoding = tiktoken.get_encoding("cl100k_base")
        num_tokens = len(encoding.encode(args))
        await message.reply(f"Number of tokens in text: {num_tokens}")
