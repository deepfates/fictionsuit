import json
from ..utils import split_text, get_embeddings
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
