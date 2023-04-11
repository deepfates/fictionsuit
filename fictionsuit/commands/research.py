from .. import config
from ..core.core import scrape_link, summarize
from ..core.user_message import UserMessage
from .command_group import CommandGroup
from ..core.core import summarize, scrape_link
from ..db.supa_tools import (
    upload_document,
    upload_document_embeddings,
    get_documents,
    delete_document,
    check_if_document_exists,
    get_summary,
)
from ..db.search import (
    create_mappings,
    embed_query,
    get_cosine_similarity,
    get_document_data,
    render_document_data,
    set_cache_needs_update,
)
from .command_group import CommandGroup


class Research(CommandGroup):
    async def cmd_read(self, message: UserMessage, args: str) -> str:
        """Returns a summary of the linked article.
        If the environment variable UPLOAD_TO_SUPABASE is defined, the article will be uploaded to the database.
        Usage:
        `read {uri of article}`"""
        document_exists = await check_if_document_exists(args)
        if document_exists:
            summary = await get_summary(document_exists)
            await message.reply(summary)
        else:
            await message.reply("scraping...")
            document = await scrape_link(args)
            await message.reply("scraping done, now summarizing...")
            summary = await summarize(document)
            await message.reply(summary)
            if config.UPLOAD_TO_SUPABASE:
                document_id = await upload_document(document, args, summary)
                await upload_document_embeddings(document, document_id)
                set_cache_needs_update()
                await message.reply(
                    f"document uploaded to Supabase with ID: {document_id}"
                )

    async def cmd_scrape(self, message: UserMessage, args: str):
        """Scrapes a web page and returns the text.
        Usage:
        `scrape {uri}`"""
        document = await scrape_link(args)
        return document.cleaned_text

    async def cmd_list_documents(self, message, args):
        """Lists all documents in the database.
        Usage:
        `list_documents`"""
        documents = await get_documents()
        ar_list = ""
        for document in documents:
            ar_list += (
                f"- {document['title']} <{document['url']}> id: {document['id']}\n"
            )
        return ar_list

    async def cmd_delete_document(self, message, args):
        """Deletes a document from the database.
        Usage:
        `delete_document {document id}`"""
        document_id = args
        await delete_document(document_id)
        set_cache_needs_update()
        await message.reply(f"document <{document_id}> deleted from database")

    async def cmd_search(self, message, args):
        """Searches for documents in the database with similar embeddings to the query.
        Usage:
        `search {query}`"""
        query = args
        embeddings_list, id_mappings = create_mappings()
        query_embedding = await embed_query(query)
        matched_documents = await get_cosine_similarity(
            2, embeddings_list, id_mappings, query_embedding
        )
        search_results = await get_document_data(matched_documents)
        document_blurbs = await render_document_data(search_results)
        res_string = f"**__Search Results for {query}__**\n"
        res_string += document_blurbs
        return res_string
