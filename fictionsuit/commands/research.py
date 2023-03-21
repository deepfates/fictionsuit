from commands.command_group import CommandGroup
from core.core import summarize, scrape_link

class Research(CommandGroup): 
    async def cmd_summarize(self, message, args):
        """**__Summarize__**
        `prefix summarize` - returns a summary of the linked article
        """
        summary = await summarize(args)
        await message.reply(summary)
 
    async def cmd_scrape(self, message, args):
        """**__Scrape__**
        `prefix scrape` - returns scraped URL
        """
        summary = await scrape_link(args)
        await message.reply(summary.cleaned_text)

