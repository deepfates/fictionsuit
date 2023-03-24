from .. import config
from .command_group import CommandGroup
from ..core.core import summarize, scrape_link
from ..api_wrap.user_message import UserMessage
from ..db.simplersupa import (
    upload_article_with_embeddings,
    search_similar,
)


class Research(CommandGroup):
    def __init__(self, annoy_index, id_mapping, id_mapping_chunk):
        self.annoy_index = annoy_index
        self.id_mapping = id_mapping
        self.id_mapping_chunk = id_mapping_chunk
        super().__init__()

    async def cmd_summarize(self, message: UserMessage, args: str):
        """**__Summarize__**
        `prefix summarize` - returns a summary of the linked article
        """
        article = await scrape_link(args)
        if config.UPLOAD_TO_SUPABASE:
            await upload_article_with_embeddings(
                article, args, self.annoy_index, self.id_mapping, self.id_mapping_chunk
            )

        # Add print statements to see the state of the instance attributes after updating
        summary = await summarize(args)
        await message.reply(summary)

    async def cmd_scrape(self, message: UserMessage, args: str):
        """**__Scrape__**
        `prefix scrape` - returns scraped URL
        """
        article = await scrape_link(args)
        if config.UPLOAD_TO_SUPABASE:
            await upload_article_with_embeddings(article, args, self.id_mapping)

        await message.reply(article.cleaned_text)

    async def cmd_recall(self, message, args):
        """**__Recall__**
        `prefix recall` - returns results of a similarity search
        """
        _, search_str = await search_similar(
            args, self.annoy_index, self.id_mapping, self.id_mapping_chunk
        )
        await message.reply(search_str)
