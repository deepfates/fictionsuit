# from .. import split_text, get_embeddings
from ..utils import split_text, get_embeddings
from .. import config
import numpy as np
import faiss
import ast

from .supa_client import init_supa_client


async def embed_query(query):
    # Split the query into chunks if necessary
    query_chunks = split_text(query)

    # Generate embeddings for each chunk
    embeddings = []
    for chunk in query_chunks:
        embedding = get_embeddings(chunk)
        embeddings.append(embedding)

    # If there's more than one chunk, average the embeddings
    if len(embeddings) > 1:
        avg_embedding = [sum(x) / len(x) for x in zip(*embeddings)]
    else:
        avg_embedding = embeddings[0]

    return avg_embedding


def create_mappings():

    if not config.embeddings_cache["needs_update"]:
        return (
            config.embeddings_cache["embeddings_list"],
            config.embeddings_cache["id_mappings"],
        )
    client = init_supa_client()
    response, _ = client.table("article_vectors").select("*").execute()
    _, data = response
    embeddings_list = []  # just raw vectors here
    id_mappings = []  # list of dicts with article_id and chunk_index
    for row in data:
        embeddings_list.append(ast.literal_eval(row["embedding"]))
        id_mappings.append({"id": row["article_id"], "chunk_idx": row["chunk_index"]})
    # Update the cache
    config.embeddings_cache["embeddings_list"] = embeddings_list
    config.embeddings_cache["id_mappings"] = id_mappings
    config.embeddings_cache["needs_update"] = False
    return embeddings_list, id_mappings


def set_cache_needs_update():
    config.embeddings_cache["needs_update"] = True


async def get_cosine_similarity(
    num_results, embeddings_list, id_mappings, query_embedding
):
    try:
        # get xb, the database embeddings
        xb = np.array(embeddings_list, dtype="float32")

        # get xq, the query embedding
        xq = np.array([query_embedding], dtype="float32")
        d = len(embeddings_list[0])  # dimension

        index = faiss.IndexFlatIP(d)  # cosine similarity
        index.add(xb)
        D, I = index.search(xq, num_results)
        # D is the distance, I is the IDs of the nearest neighbors
        # Note: in the future, passing along chunk indices will allow us to
        # return the most relevant chunk of the article
        matched_articles = []
        for i, embed_idx in enumerate(I[0]):
            matched_article = id_mappings[embed_idx]
            if matched_article["id"] not in [a["id"] for a in matched_articles]:
                matched_article["similarity"] = D[0][i]
                matched_articles.append(matched_article)
        return matched_articles
    except Exception as e:
        print(e)
        return e, None


async def get_article_blurbs(
    query, matched_articles
):  # where ids is a list of article IDs
    try:
        client = init_supa_client()
        article_ids = [article["id"] for article in matched_articles]
        response, _ = (
            client.table("articles").select("*").in_("id", article_ids).execute()
        )
        _, data = response
        res_string = f"**__Search Results for {query}__**\n" ""
        for article in data:
            res_string += (
                f"- {article['title']} <{article['url']}> - {article['ai_summary']}\n"
            )
        return res_string
    except Exception as e:
        print(e)
        return e, None


async def search_similar(matched_articles):
    pass
