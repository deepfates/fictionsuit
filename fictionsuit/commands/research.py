from ..core.user_message import UserMessage
from .. import config
from .command_group import CommandGroup
from ..core.core import summarize, scrape_link
from ..db.supa_tools import (
    upload_article,
    upload_article_embeddings,
    get_articles,
    delete_article,
)
from ..db.search import (
    embed_query,
    create_mappings,
    get_cosine_similarity,
    get_article_blurbs,
    set_cache_needs_update,
)


class Research(CommandGroup):
    async def cmd_read(self, message: UserMessage, args: str):
        """**__Read__**
        `prefix read` - returns a summary of the linked article, uploads, and embeds
        """
        article = await scrape_link(args)
        # should prepend the title, author, metadata, date, url to the cleaned_text of the file too
        summary = await summarize(args)
        await message.reply(summary)
        if config.UPLOAD_TO_SUPABASE:
            article_id = await upload_article(article, args, summary)
            await upload_article_embeddings(article, article_id)
            set_cache_needs_update()
            await message.reply(f"Article uploaded to Supabase with ID: {article_id}")

    async def cmd_scrape(self, message: UserMessage, args: str):
        """**__Scrape__**
        `prefix scrape` - returns scraped URL
        """
        article = await scrape_link(args)
        await message.reply(article.cleaned_text)

    async def cmd_list_articles(self, message, args):
        """**__Recall__**
        `prefix list_articles` - returns a list of all articles in the database
        """
        articles = await get_articles()
        ar_list = ""
        for article in articles:
            ar_list += f"- {article['title']} <{article['url']}> id: {article['id']}\n"
        await message.reply(ar_list)

    async def cmd_delete_article(self, message, args):
        """**__Delete__**
        `prefix delete_article` - deletes an article from the database
        """
        article_id = args
        await delete_article(article_id)
        set_cache_needs_update()
        await message.reply(f"Article <{article_id}> deleted from database")

    async def cmd_search(self, message, args):
        """**__Search__**
        `prefix search` - searches for similar articles in the database"""
        query = args
        embeddings_list, id_mappings = create_mappings()
        query_embedding = await embed_query(query)
        matched_articles = await get_cosine_similarity(
            2, embeddings_list, id_mappings, query_embedding
        )
        search_results = await get_article_blurbs(query, matched_articles)
        await message.reply(search_results)
