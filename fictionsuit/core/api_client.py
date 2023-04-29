import asyncio
import sys
import time
from io import TextIOBase
from typing import List

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio
from hypercorn.config import Config
from hypercorn.asyncio import serve

from ..commands.command_group import CommandHandled

from .fictionscript.fictionscript import FictionScript

from .fictionscript.scope import Scope

from ..commands.failure import CommandFailure

from .. import config
from ..api_wrap.openai import ApiMessages
from .system import System
from .user_message import UserMessage


class ApiClient:
    def __init__(self, system: System):
        self.system: System = system

    def run(self):
        app = FastAPI()

        app.add_middleware(
            CORSMiddleware,
            allow_origins=["http://localhost:5173"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"]
        )

        @app.post("/fic")
        async def fic(request: RequestBody):
            if request.request_text is None:
                return {"error": "no request text"}
            if request.user_name is None:
                return {"error": "no user name"}

            result = await self.system.enqueue_message(
                ApiMessage(self, request), return_whatever=True
            )

            if result is None or isinstance(result, CommandHandled):
                return {"schema": "nothing"}

            if isinstance(result, CommandFailure):
                return {"schema": "failure", "explanation": result}

            if isinstance(result, str):
                return {"schema": "text", "value": result}

            if isinstance(result, FictionScript):
                return {"schema": "script", "code": "\n".join(result.lines)}

            return {"schema": "other", "description": f"{result}"}

        asyncio.run(serve(app, Config()))


class RequestBody(BaseModel):
    user_name: str | None
    request_text: str | None


class ApiMessage(UserMessage):
    """Wraps an api request to the system."""

    def __init__(self, client: ApiClient, request: RequestBody):
        super().__init__(
            request.request_text, request.user_name
        )  # TODO: user accounts, authentication, etc
        self.client = client
        self.request = request
        self.timestamp = time.time()

    async def _send(self, message_content: str) -> bool:
        pass  # TODO: websockets or something

    async def _reply(self, reply_content: str) -> bool:
        pass

    async def _react(self, reaction: str | None) -> bool:
        pass

    async def _undo_react(self, reaction: str | None) -> bool:
        pass

    async def _get_timestamp(self) -> float:
        return self.timestamp
