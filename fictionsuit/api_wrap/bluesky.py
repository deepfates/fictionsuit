import datetime
import discord
from discord import Message
from discord.ext import commands
import requests

from .. import config
from ..core.system import System
from ..core.user_message import UserMessage
from .openai import ApiMessages, api_message

from atprototools import Session

import time


class BlueskyClient:
    def __init__(
        self,
        username: str = config.BSKY_USERNAME,
        password: str = config.BSKY_PASSWORD,
        #    system: System,
        #    command_prefix=config.COMMAND_PREFIX
    ):
        # self.system = system
        # self.command_prefix = command_prefix
        self.session = Session(username, password)

    def notification_count(self):
        headers = {"Authorization": "Bearer " + self.session.ATP_AUTH_TOKEN}
        resp = requests.get(
            self.session.ATP_HOST + "/xrpc/app.bsky.notification.getUnreadCount",
            headers=headers,
        )
        if resp.ok:
            return resp.json()["count"]

    async def sm_default(self, args):
        return f"{self.notification_count()} notifications."

    async def sm_inspect(self, args):
        return (
            f"**Bluesky client**\nDID `{self.session.DID}`\n@ `{self.session.USERNAME}`"
        )

    async def sm_check(self, args):
        return self.get_notifications()

    def get_notifications(self, n=10):
        headers = {"Authorization": "Bearer " + self.session.ATP_AUTH_TOKEN}
        resp = requests.get(
            self.session.ATP_HOST
            + f"/xrpc/app.bsky.notification.listNotifications?limit={n}",
            headers=headers,
        )
        if resp.ok:
            # mark_seen = {"seenAt": self._time()}
            # requests.post(
            #     self.session.ATP_HOST + f"/xrpc/app.bsky.notification.updateSeen",
            #     headers=headers,
            #     json=mark_seen,
            # )
            return {  # TODO: the reason this isn't working is because the api is returning it as a schema: other of itself. i think. idfk
                # also, in the api, remove the json prettifier stuff.
                "schema": "script",
                "code": resp.text,
                "language": "json",
                "source_file": "",
            }

    def _time(self):
        timestamp = datetime.datetime.now(datetime.timezone.utc)
        timestamp = timestamp.isoformat().replace("+00:00", "Z")
        return timestamp

    def follow(self, did):
        headers = {"Authorization": "Bearer " + self.session.ATP_AUTH_TOKEN}
        follow_request = {
            "collection": "app.bsky.graph.follow",
            "repo": f"{self.session.DID}",
            "record": {
                "$type": "app.bsky.graph.follow",
                "createdAt": self._time(),
                "subject": did,
            },
        }
        resp = requests.post(
            self.session.ATP_HOST + f"/xrpc/com.atproto.repo.createRecord",
            headers=headers,
            json=follow_request,
        )
        if resp.ok:
            return resp.json()

    def run(self):
        while True:
            if self.notification_count() > 0:
                print("notes!")
                notifications = self.get_notifications()
                for notification in notifications:
                    print(notification)
                    if notification["reason"] == "follow":
                        pass  # TODO: put in a check to make sure we're not already following them
                        # otherwise it'll keep pinging them lmao
                        # also, figure out how to clear notifications!
                        # self.follow(notification["author"]["did"])
                    if notification["reason"] == "mention":
                        pass
            # skoots = self.session.get_latest_n_skoots('bsky.app', 3).json()
            # print(skoots)
            time.sleep(10)


class BlueskyClientFactory:
    async def sm_default(self, content):
        return BlueskyClient()


# class BlueskyMessage(UserMessage):
#     def __init__(self, client: BlueskyClient, message: Message):
#         self.discord_message = message
#         super().__init__(message.content, message.author.name)
#         self.char_limit = 2000
#         self.client = client

#     async def set_nickname(self, nickname: str):
#         await self.client.set_nickname(self.discord_message.guild, nickname)

#     async def _send(self, message_content: str) -> bool:
#         try:
#             result = await self.discord_message.channel.send(message_content)
#             return result is not None
#         except Exception as e:
#             print(f"Exception in discord message send: {e}")
#             return False

#     async def _react(self, reaction: str | None) -> bool:
#         if reaction is None:
#             reaction = "👍"
#         try:
#             result = await self.discord_message.add_reaction(reaction)
#             return result is not None
#         except Exception as e:
#             print(f"Exception in discord reaction: {e}")
#             return False

#     async def _undo_react(self, reaction: str | None) -> bool:
#         if reaction is None:
#             reaction = "👍"
#         try:
#             server = self.discord_message.guild
#             if server.id not in self.client.as_member_of:
#                 self.client.as_member_of[
#                     server.id
#                 ] = await self.client.get_self_as_member(server)
#             self_member = self.client.as_member_of[self.discord_message.guild.id]
#             result = await self.discord_message.remove_reaction(reaction, self_member)
#             return result is not None
#         except Exception as e:
#             print(f"Exception in discord reaction removal: {e}")
#             return False

#     async def _reply(self, reply_content: str) -> bool:
#         try:
#             result = await self.discord_message.reply(reply_content)
#             return result is not None
#         except Exception as e:
#             print(f"Exception in discord message send: {e}")
#             return False

#     async def _retrieve_history(
#         self,
#         limit: int = 10,
#     ) -> ApiMessages:
#         messages = []
#         history = self.discord_message.channel.history(
#             before=self.discord_message, limit=limit
#         )
#         async for msg in history:
#             if msg.author == self.client.user:
#                 role = "assistant"
#                 content = msg.content
#             else:
#                 role = "user"
#                 content = f"{msg.author.name}: " + msg.content

#             messages += api_message(role, content)

#         messages.reverse()

#         return messages

#     async def _get_timestamp(self) -> float:
#         return self.discord_message.created_at.timestamp()
