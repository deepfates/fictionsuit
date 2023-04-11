import time

import tiktoken

from .. import config
from ..core.user_message import UserMessage
from .command_group import CommandGroup


class Debug(CommandGroup):
    async def cmd_ping(self, message: UserMessage, args: str) -> str:
        """Returns the one-way latency from the user to the bot.
        Usage:
        `ping`"""
        timestamp = await message.get_timestamp()
        now = time.time()
        latency = round(now - timestamp)
        response = f"Pong! Latency {latency} ms"
        return response

    async def cmd_lorem(self, message: UserMessage, args: str) -> str:
        """Returns a few paragraphs of lorem ipsum.
        Usage:
        `lorem`"""
        return "\n".join(
            paragraph.strip()
            for paragraph in """
            Lorem ipsum dolor sit amet, consectetur adipiscing elit. Ut faucibus nibh quam, non interdum mi egestas id. Nam dapibus mattis metus, sed lacinia risus eleifend ac. Suspendisse et neque orci. Nulla molestie a magna ac gravida. Ut commodo ut est eleifend suscipit. Proin varius interdum nulla sit amet imperdiet. Suspendisse id ultricies urna. Nulla facilisi. Vivamus luctus ac nisl vitae rhoncus. Vivamus in pulvinar est. Donec dictum faucibus interdum.

            Vivamus vitae nibh arcu. Donec massa dolor, posuere a auctor id, ultricies ut turpis. Etiam placerat sem eu consectetur consectetur. Donec consequat, nunc ut maximus dignissim, eros orci dictum magna, at placerat ligula ipsum a nisl. In sit amet vestibulum eros, rutrum pulvinar est. Nullam iaculis velit quis nulla lacinia, eu hendrerit lectus commodo. Maecenas ut imperdiet nisi, at bibendum leo.

            Praesent non fermentum metus. Sed vulputate metus id nulla vestibulum luctus. Nam vitae augue erat. Duis vestibulum, erat dignissim malesuada malesuada, nisl nisl egestas neque, sed eleifend dui urna in eros. Fusce efficitur porta condimentum. Suspendisse tincidunt magna sagittis pretium pharetra. Vestibulum sodales, metus id porta elementum, velit quam malesuada nisi, vitae varius metus felis sit amet tellus. Duis vel pulvinar magna. Duis non iaculis magna, tempor ultrices neque. Cras odio urna, hendrerit sed sodales a, pharetra sed purus.

            Morbi lobortis lorem est, et commodo nisl blandit quis. Fusce vel velit et arcu fringilla fringilla pulvinar eget nisl. Quisque viverra sagittis ex, sit amet malesuada odio finibus sed. Sed commodo consectetur mi convallis scelerisque. Suspendisse iaculis libero vitae augue porttitor, vel mollis dui facilisis. Nulla et suscipit urna. Phasellus commodo rutrum magna, quis ultricies purus posuere sit amet.

            Vivamus porta in mi hendrerit consequat. Integer blandit placerat dui ut porta. Sed congue dolor leo, vel interdum ante posuere non. Proin dignissim vitae ligula vel interdum. Aliquam at nunc non felis dapibus placerat. Aliquam id tempus sapien. Morbi tempor luctus mauris sed consectetur. Etiam sagittis pharetra pellentesque.
        """.split(
                "\n"
            )
        )

    async def cmd_react(self, message: UserMessage, args: str) -> None:
        """Reacts to the message.
        Usage:
        `react`
        `react {emoji}`"""
        await message.react()

    async def cmd_react_then_unreact(self, message: UserMessage, args: str) -> None:
        """Reacts to the message, waits a second, then removes the reaction.
        Usage:
        `react_then_unreact`"""
        await message.react()
        time.sleep(1)
        await message.undo_react()

    async def cmd_echo(self, message: UserMessage, args: str) -> str:
        """Returns the arguments.
        Usage:
        `echo {text}`"""
        return args

    async def cmd_yell(self, message: UserMessage, args: str) -> str:
        """Returns the arguments, and replies to the message.
        This is distinct from echo in that it will reply even when called from within a script, which would normally disable replies.
        This should pretty much only be used for debugging, and should not appear in finished scripts.
        """
        previous_state = message.disable_interactions
        message.disable_interactions = False
        await message.reply(args)
        message.disable_interactions = previous_state
        return args

    # TODO: a more graceful cmd_exit would be nice - one that shuts the process down in a more controlled manner
    async def cmd_kill(self, message: UserMessage, args: str) -> None:
        """Immediately and unceremoniously kills the entire python process.
        Usage:
        `kill`"""
        exit()

    async def cmd_tokens(self, message: UserMessage, args: str) -> int:
        """Returns the number of tokens in the `cl100k_base` tiktoken encoding of the given text.
        Usage:
        `tokens {text}`"""
        try:
            encoding = tiktoken.encoding_for_model(config.OAI_MODEL)
        except KeyError:
            encoding = tiktoken.get_encoding("cl100k_base")
        num_tokens = len(encoding.encode(args))
        await message.reply(f"Number of tokens in text: {num_tokens}")
        return num_tokens
