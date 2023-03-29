import json
from ..utils import split_text, get_embeddings, get_chat_completion
from .supa_client import init_supa_client


async def upload_document(document, url, summary, type="article"):
    client = init_supa_client()

    try:
        document_dict = {
            "type": type,
            "title": document.title,
            "meta_description": document.meta_description,
            "url": url,
            "ai_summary": summary,
            "chunks": json.dumps(
                {
                    str(i): chunk
                    for i, chunk in enumerate(split_text(document.cleaned_text))
                }
            ),
        }
        res, _ = client.table("documents").insert(document_dict).execute()
        _, data = res
        document_id = data[0]["id"]

        return document_id

    except Exception as e:
        print(e)
        return e, None


async def upload_document_embeddings(scraped_document, document_id):
    client = init_supa_client()

    for i, chunk in enumerate(split_text(scraped_document.cleaned_text)):
        embedding = get_embeddings(chunk)
        vector_data = {
            "embedding": embedding,
            "chunk_index": i,
            "document_id": document_id,
        }
        client.table("document_vectors").insert(vector_data).execute()


async def get_documents():
    client = init_supa_client()
    res, _ = client.table("documents").select("*").execute()
    _, data = res
    return data


async def delete_document(document_id):
    client = init_supa_client()
    res, _ = client.table("documents").delete().eq("id", document_id).execute()
    _, data = res
    return data


async def check_if_document_exists(url):
    client = init_supa_client()
    res, _ = client.table("documents").select("*").eq("url", url).execute()
    _, data = res
    return data


async def get_summary(data):
    res_string = ""
    for document in data:
        res_string += f"- {document['ai_summary']}\n"
    return res_string


async def get_tags():
    client = init_supa_client()
    res, _ = client.table("tags").select("*").execute()
    _, data = res
    return data


async def check_if_tag_exists(tag):
    client = init_supa_client()
    res, _ = client.table("tags").select("*").eq("name", tag).execute()
    _, data = res
    return data


async def get_tags_from_text(text, n_tags=3):
    try:
        # query all tags in supabase
        existing_tags = await get_tags()
        # turn the tags into a string
        existing_tags = [tag["name"] for tag in existing_tags]

        tag_string = ", ".join(existing_tags)
        tag_prompt = f"""Your job is to create a list of {n_tags} tags separated by a comma and a space (tag1, tag2) that accurately categorize this text. *Important*: Try to be as concise as possible. Shorter words are better.
        *Important*: You can use any tags you want, but you should always try your best to use tags that are already in the database.     
        Tags in database: {tag_string}
        Text: {text}
        Tags:"""
        tag_completion = await get_chat_completion(tag_prompt)
        # turn the tags into a list
        tag_completion = tag_completion.split(", ")
        # upload these tags to supa
        return tag_completion
    except Exception as e:
        print(e)
        return [e]


async def upload_tags(tags, document_id):
    client = init_supa_client()
    for tag in tags:
        existing_tag = await check_if_tag_exists(tag)
        if existing_tag:
            tag_id = existing_tag[0]["id"]
            client.table("tags_docs_ref").insert(
                {"tag_id": tag_id, "doc_id": document_id}
            ).execute()
        else:
            tag_data = {
                "name": tag,
            }
            res, _ = client.table("tags").insert(tag_data).execute()
            _, data = res

            client.table("tags_docs_ref").insert(
                {"tag_id": data[0]["id"], "doc_id": document_id}
            ).execute()
