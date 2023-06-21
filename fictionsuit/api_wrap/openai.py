from __future__ import annotations

import aiohttp
import openai

from ..core.fictionscript.scope import Scope

from ..commands.failure import CommandFailure

from .. import config

ApiMessages = list[dict[str, str]]

OPENAI_COMPLETIONS_ENDPOINT = "https://api.openai.com/v1/chat/completions"

ESCAPES = ["``COM", "```COM", "``MSG", "``OBJ"]


class ChatInstance:
    # TODO: there are a few optional parameters like logprobs that we might want to make use of
    def __init__(
        self,
        model: str = config.OAI_MODEL,
        temperature: float = 1.0,
        max_tokens: int = 500,
        top_p: float = 1.0,
        name: str = "anon",
    ):
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.top_p = top_p
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {openai.api_key}",
        }
        self.body = {}
        self.history = []
        self.name = name

    async def sm_inspect(self, _):
        return f'ChatInstance **{self.name}**\nUsing model "{self.model}"\nMax {self.max_tokens} tokens per response\nTemperature = {self.temperature}\nTop P = {self.top_p}\n\nHistory: {len(self.history)} messages (try `<{self.name}??>` for full history)'

    def __str__(self):
        return f"ChatInstance {self.name}"

    def __repr__(self):
        return f"<ChatInstance {self.name}>"

    def _body(self, messages: ApiMessages, n: int) -> dict:
        return {
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "top_p": self.top_p,
            "messages": messages,
            "n": n,
        }

    async def sm_script(self, args):
        out = []
        out.append(f"<chat> {self.name}")
        out.append(f"<model @ {self.name}> {self.model}")
        out.append(f"<temp @ {self.name}> {self.temperature}")
        out.append(f"<top_p @ {self.name}> {self.top_p}")
        out.append(f"<limit @ {self.name}> {self.max_tokens}")
        for message in self.history:
            content = message["content"]
            if "\n" in content:
                content = content.replace("\n", "---\n", 1) + "--"
            content.replace("{", "{{")
            content.replace("}", "}}")
            out.append(f"<{message['role']} @ {self.name}> {content}")
        out.append(f"return | {self.name}")
        return "\n".join(out)

    async def sm_last(self, args):
        if args == "":
            return self.history[-1]["content"]
        try:
            n = int(args)
        except:
            return CommandFailure(f'Expected an integer, got "{args}".')
        if n < 1:
            return CommandFailure(f'Expected a positive integer, got "{n}".')
        if n == 1:
            return self.history[-1]["content"]
        last = [x["content"] for x in self.history[-n:]]
        return Scope(name=f"{self.name} last", vars={str(i): last[i] for i in range(n)})

    async def sm_default(self, content):
        await self.sm_user(content)
        return await self._continue(1)

    async def sm_retry(self, args: str):
        pass  # TODO

    async def sm_increment(self, args: str) -> str:
        if args == "":
            return await self._continue(1)
        try:
            n = int(args)
        except:
            return CommandFailure(f'Expected an integer, got "{n}".')
        if n < 1:
            return CommandFailure(f'Expected a positive integer, got "{n}".')
        return await self._continue(n)

    async def sm_decrement(self, _) -> str:
        return self.history.pop()["content"]

    async def sm_add(self, content):
        await self.sm_user(content)

    async def sm_subtract(self, n):
        try:
            n = int(n)
        except:
            return CommandFailure("Chat subtraction requires an integer argument.")
        if n < 1:
            return CommandFailure(
                "Chat subtraction requires a positive integer argument."
            )
        for _ in range(n):
            self.history.pop()

    async def sm_temp(self, temperature):
        try:
            temperature = float(temperature)
        except:
            return CommandFailure("Chat temperature must be a number.")
        self.temperature = temperature

    async def sm_limit(self, limit):
        try:
            limit = int(limit)
        except:
            return CommandFailure("Chat token limit must be an integer.")
        self.max_tokens = limit

    async def sm_top_p(self, top_p):
        try:
            top_p = float(top_p)
        except:
            return CommandFailure("Chat Top-P must be a number.")
        self.top_p = top_p

    async def sm_model(self, model):
        self.model = model

    async def sm_dump(self, _) -> str:
        formatted_messages = [
            f'**__{m["role"]}__**:\n{m["content"]}\n' for m in self.history
        ]
        return "\n".join(formatted_messages)

    # named this way because continue is a reserved word
    async def _continue(self, n: int = 1) -> str | list[str]:
        completion = await self._get_completion(self.history, n)

        if "error" in completion:
            raise Exception(f"OpenAI completion error:\n\n{completion['error']}")

        try:
            response = [
                completion["choices"][x]["message"]["content"].strip() for x in range(n)
            ]
        except:
            raise Exception(f"Failed parsing openai completion:\n\n{completion}\n")

        if n == 1:
            self.history.extend(api_message("assistant", response[0]))
            return response[0]

        response = Scope(
            name=f"{self.name} continuations",
            vars={str(i): response[i] for i in range(n)},
        )

        return response

    async def sm_user(self, content):
        self.history.extend(api_message("user", content))

    async def sm_system(self, content):
        self.history.extend(api_message("system", content))

    async def sm_assistant(self, content):
        self.history.extend(api_message("assistant", content))

    async def _get_completion(self, messages: ApiMessages, n: int) -> dict:
        body = self._body(messages, n)

        async with aiohttp.ClientSession() as session:
            async with session.post(
                OPENAI_COMPLETIONS_ENDPOINT, headers=self.headers, json=body
            ) as response:
                response_data = await response.json()

        return response_data


class ChatFactory:
    async def sm_default(self, content):
        return ChatInstance(name=content)


def api_message(role: str, content: str) -> ApiMessages:
    return [{"role": role, "content": content}]
