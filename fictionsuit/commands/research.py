from .command_group import CommandGroup
from ..core.core import summarize, scrape_link
from ..api_wrap.user_message import UserMessage


class Research(CommandGroup):
    async def cmd_summarize(self, message: UserMessage, args: str) -> str:
        """**__Summarize__**
        `prefix summarize` - returns a summary of the linked article
        """
        summary = await summarize(args)
        await message.reply(summary)
        return summary

    async def cmd_scrape(self, message: UserMessage, args: str) -> str:
        """**__Scrape__**
        `prefix scrape` - returns scraped URL
        """
        summary = await scrape_link(args)
        await message.reply(summary.cleaned_text)
        return summary
