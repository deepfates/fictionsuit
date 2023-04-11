import asyncio
import sys
import time
from io import TextIOBase

from .. import config
from ..api_wrap.openai import ApiMessages
from .system import System
from .user_message import UserMessage


class TextIOClient:
    def __init__(
        self,
        system: System,
        text_in: TextIOBase = sys.stdin,
        text_out: TextIOBase = sys.stdout,
        cli: bool = True,
        reactions: bool = False,
    ):
        self.system = system
        self.text_in = text_in
        self.text_out = text_out
        self.cli = cli
        self.skip_next_newline = True  # To avoid duplicating newlines from user input.
        self.reactions = reactions

    def run(self):
        asyncio.run(self._run())

    async def _run(self):
        greeting = ""
        input_indicator = ""
        if self.cli:
            greeting = f"Welcome to Fictionsuit CLI."
            input_indicator = "\n> "
            self.print(f"{greeting}{input_indicator}")
            self.skip_next_newline = True
        try:
            message_lines = []
            auto_collecting = False
            for line in self.text_in:
                line = line.rstrip()
                if not auto_collecting and line.endswith("--"):
                    if line[-3] == "-":
                        auto_collecting = True
                        self.text_out.write("--> ")
                        self.text_out.flush()
                        message_lines.append(line[:-3].rstrip())
                        continue
                    self.text_out.write("--> ")
                    self.text_out.flush()
                    message_lines.append(line[:-2].rstrip())
                    continue
                if auto_collecting:
                    if not line.endswith("--"):
                        self.text_out.write("--> ")
                        self.text_out.flush()
                        message_lines.append(line)
                        continue
                    auto_collecting = False
                    line = line[:-2].rstrip()

                message_lines.append(line)
                wrap = TextIOMessage(self, "\n".join(message_lines))
                message_lines = []
                wrap.no_react = not self.reactions
                await self.system.enqueue_message(wrap)
                self.text_out.write(input_indicator)
                self.text_out.flush()
                self.skip_next_newline = self.cli
        except KeyboardInterrupt:
            if self.cli:
                self.text_out.write("\nShutting down due to keyboard interrupt.")
        self.text_out.write("\n")
        self.text_out.flush()

    def print(self, string: str):
        if self.skip_next_newline:
            self.skip_next_newline = False
        else:
            self.text_out.write("\n")
        self.text_out.write(string)
        self.text_out.flush()


class TextIOMessage(UserMessage):
    """Wraps an input from stdin"""

    def __init__(self, client: TextIOClient, content):
        super().__init__(content, "User")  # TODO: config entry for CLI username?
        self.client = client
        self.timestamp = time.time()

    async def _send(self, message_content: str) -> bool:
        try:
            self.client.print(message_content)
            return True
        except Exception as e:
            print(f"Exception in TextIO out: {e}")
            return False

    async def _reply(self, reply_content: str) -> bool:
        return await self._send(reply_content)

    async def _react(self, reaction: str | None) -> bool:
        return await self._send(f'<reaction "{reaction}">')

    async def _undo_react(self, reaction: str | None) -> bool:
        return await self._send(f'<undo reaction "{reaction}">')

    async def _get_timestamp(self) -> float:
        return self.timestamp
