from ...api_wrap import UserMessage
from ...core import OpenAIChat


class ScriptMessage(UserMessage):
    def __init__(self, content: str, filename: str, invoker: UserMessage):
        super().__init__(content, f"script: {filename}")
        self.invoker = invoker
        self.disable_interactions = invoker.disable_interactions

    async def _send(self, message_content: str) -> bool:
        return await self.invoker._send(message_content)

    async def _reply(self, reply_content: str) -> bool:
        return await self.invoker._reply(reply_content)

    async def _react(self, reaction: str | None) -> bool:
        return await self.invoker._react(reaction)

    async def _undo_react(self, reaction: str | None) -> bool:
        return await self.invoker._undo_react(reaction)

    async def _get_timestamp(self) -> float:
        return await self.invoker._get_timestamp()

    async def _retrieve_history(self) -> OpenAIChat:
        return await self.invoker._retrieve_history()
