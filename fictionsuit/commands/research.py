from .command_group import CommandGroup
from ..core.core import summarize, scrape_link
from ..api_wrap.user_message import UserMessage
from ..db.supa import supabase, list_first_article


class Research(CommandGroup):
    async def cmd_summarize(self, message: UserMessage, args: str):
        """**__Summarize__**
        `prefix summarize` - returns a summary of the linked article
        """
        summary = await summarize(args)
        await message.reply(summary)

    async def cmd_scrape(self, message: UserMessage, args: str):
        """**__Scrape__**
        `prefix scrape` - returns scraped URL
        """
        summary = await scrape_link(args)
        await message.reply(summary.cleaned_text)

    async def cmd_supa(self, message, args):
        """**__Supa__**
        `prefix supa` - returns supabase stats
        """
        res = await list_first_article()
        await message.reply(res)
