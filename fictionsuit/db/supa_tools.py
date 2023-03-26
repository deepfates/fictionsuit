import ast
import json
from ..utils import split_text, get_embeddings
from .. import config
from .supa_client import init_supa_client


async def upload_article(article, url, summary):
    client = init_supa_client()

    try:
        article_dict = {
            "title": article.title,
            "meta_description": article.meta_description,
            "url": url,
            "ai_summary": summary,
            "chunks": json.dumps(
                {
                    str(i): chunk
                    for i, chunk in enumerate(split_text(article.cleaned_text))
                }
            ),
        }

        res, _ = client.table("articles").insert(article_dict).execute()
        _, data = res
        article_id = data[0]["id"]

        return article_id

    except Exception as e:
        print(e)
        return e, None


async def upload_article_embeddings(scraped_article, article_id):
    client = init_supa_client()

    for i, chunk in enumerate(split_text(scraped_article.cleaned_text)):
        embedding = get_embeddings(chunk)
        vector_data = {
            "embedding": embedding,
            "chunk_index": i,
            "article_id": article_id,
        }
        client.table("article_vectors").insert(vector_data).execute()


async def get_articles():
    client = init_supa_client()
    res, _ = client.table("articles").select("*").execute()
    _, data = res
    return data


async def delete_article(article_id):
    client = init_supa_client()
    res, _ = client.table("articles").delete().eq("id", article_id).execute()
    _, data = res
    return data
