from __future__ import annotations

from ...core.user_message import UserMessage


class ScriptLineMessage(UserMessage):
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


class ExpressionMessage(UserMessage):
    def __init__(self, content: str, context: str, invoker: UserMessage):
        super().__init__(content, f"expression: {context}")
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
