from api_wrap.user_message import UserMessage

class DiscordMessage(UserMessage):
    '''Wraps a discord message for platform-agnostic use.'''

    def __init__(self, message):
        self.discord_message = message
        super().__init__(message.content, message.author.name)
        self.char_limit = 2000

    async def _reply(self, reply_content):
        try:
            result = await self.discord_message.reply(reply_content)
            return result is not None
        except Exception as e:
            print(f'Exception in discord message send: {e}')
            return False

    async def _get_timestamp(self):
        return self.discord_message.created_at.timestamp()
