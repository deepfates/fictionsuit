from ..core.system import System
from ..api_wrap.user_message import UserMessage
from io import TextIOBase
from .. import config
import sys
import time
import asyncio

class TextIOClient():
    def __init__(
        self,
        system: System,
        text_in: TextIOBase = sys.stdin,
        text_out: TextIOBase = sys.stdout,
        cli: bool = True
        ):
        self.system = system
        self.text_in = text_in
        self.text_out = text_out
        self.cli = cli
        self.skip_next_newline = True # To avoid duplicating newlines from user input. 

    def run(self):
        asyncio.run(self._run())

    async def _run(self):
        greeting = ''
        input_indicator = ''
        if self.cli:
            greeting = f'Welcome to Fictionsuit CLI. The command prefix is "{config.COMMAND_PREFIX}"'
            input_indicator = '\n> '
            self.print(f'{greeting}{input_indicator}')
            self.skip_next_newline = True
        try:
            for line in self.text_in:
                wrap = TextIOMessage(self, line)
                await self.system.enqueue_message(wrap)
                self.text_out.write(input_indicator)
                self.text_out.flush()
                self.skip_next_newline = self.cli
        except KeyboardInterrupt:
            if self.cli:
                self.text_out.write('\nShutting down due to keyboard interrupt.')
        self.text_out.write('\n')
        self.text_out.flush()

    def print(self, string: str):
        if self.skip_next_newline:
            self.skip_next_newline = False
        else:
            self.text_out.write('\n')
        self.text_out.write(string)
        self.text_out.flush()


class TextIOMessage(UserMessage):
    '''Wraps an input from stdin'''

    def __init__(self, client: TextIOClient, content):
        super().__init__(content, 'User') # TODO: config entry for CLI username?
        self.client = client
        self.timestamp = time.time()

    async def _send(self, message_content: str) -> bool:
        try:
            self.client.print(message_content)
            return True
        except Exception as e:
            print(f'Exception in TextIO out: {e}')
            return False

    async def _reply(self, reply_content: str) -> bool:
        return await self._send(reply_content)

    async def _react(self, reaction: str | None) -> bool:
        return await self._send(f'<reaction "{reaction}">')

    async def _undo_react(self, reaction: str | None) -> bool:
        return await self._send(f'<undo reaction "{reaction}">')

    async def _get_timestamp(self) -> float:
        return self.timestamp



if __name__ == '__main__':
    main()










