import aiohttp
import openai

from .. import config

ApiMessages = list[dict[str, str]]

OPENAI_COMPLETIONS_ENDPOINT = "https://api.openai.com/v1/chat/completions"


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

    # named this way because continue is a reserved word
    async def continue_(self, n: int = 1) -> str | list[str]:
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

        return response

    async def user(self, content):
        self.history.extend(api_message("user", content))

    async def system(self, content):
        self.history.extend(api_message("system", content))

    async def assistant(self, content):
        self.history.extend(api_message("assistant", content))

    async def _get_completion(self, messages: ApiMessages, n: int) -> dict:
        body = self._body(messages, n)

        async with aiohttp.ClientSession() as session:
            async with session.post(
                OPENAI_COMPLETIONS_ENDPOINT, headers=self.headers, json=body
            ) as response:
                response_data = await response.json()

        return response_data


def api_message(role: str, content: str) -> ApiMessages:
    return [{"role": role, "content": content}]
