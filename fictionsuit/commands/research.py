from ..core.user_message import UserMessage
from .. import config
from .command_group import CommandGroup, auto_reply
from ..core.core import summarize, scrape_link
from ..db.supa_tools import (
    upload_document,
    upload_document_embeddings,
    get_documents,
    delete_document,
    check_if_document_exists,
    get_summary,
    get_tags_from_text,
    upload_tags,
)
from ..db.search import (
    embed_query,
    create_mappings,
    get_cosine_similarity,
    get_document_data,
    render_document_data,
    set_cache_needs_update,
)


class Research(CommandGroup):
    @auto_reply
    async def cmd_read(self, message: UserMessage, args: str) -> str:
        """**__Read__**
        `prefix read` - returns a summary of the linked document, uploads, and embeds
        """
        document_exists = await check_if_document_exists(args)
        if document_exists:
            summary = await get_summary(document_exists)
            await message.reply(summary)
        else:
            document = await scrape_link(args)
            summary = await summarize(document)
            await message.reply(summary)
            # get tags
            tags = await get_tags_from_text(summary)
            await message.reply(tags)
            if config.UPLOAD_TO_SUPABASE:
                document_id = await upload_document(document, args, summary)
                await upload_document_embeddings(document, document_id)
                set_cache_needs_update()
                # upload tags to supabase
                await upload_tags(tags, document_id)

    @auto_reply
    async def cmd_scrape(self, message: UserMessage, args: str):
        """**__Scrape__**
        `prefix scrape` - returns scraped URL
        """
        document = await scrape_link(args)
        return document.cleaned_text

    @auto_reply
    async def cmd_list_documents(self, message, args):
        """**__Recall__**
        `prefix list_documents` - returns a list of all documents in the database
        """
        documents = await get_documents()
        ar_list = ""
        for document in documents:
            ar_list += (
                f"- {document['title']} <{document['url']}> id: {document['id']}\n"
            )
        return ar_list

    async def cmd_delete_document(self, message, args):
        """**__Delete__**
        `prefix delete_document` - deletes an document from the database
        """
        document_id = args
        await delete_document(document_id)
        set_cache_needs_update()
        await message.reply(f"document <{document_id}> deleted from database")

    @auto_reply
    async def cmd_search(self, message, args):
        """**__Search__**
        `prefix search` - searches for similar documents in the database"""
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
