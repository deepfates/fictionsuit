from ..api_wrap import UserMessage
from ..core import summarize
from ..db.supa import list_first_article, supabase
from ..utils import scrape_link
from .command_group import CommandGroup


class Research(CommandGroup):
    async def cmd_summarize(self, message: UserMessage, args: str) -> str:
        """Returns a summary of the linked article"""
        summary = await summarize(args)
        await message.reply(summary)
        return summary

    async def cmd_scrape(self, message: UserMessage, args: str) -> str:
        """Returns scraped URL"""
        summary = await scrape_link(args)
        await message.reply(summary.cleaned_text)
        return summary

    async def cmd_supa(self, message: UserMessage, args: str) -> str:
        """Returns supabase stats"""
        res = await list_first_article()
        await message.reply(res)
        return res
