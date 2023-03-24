from annoy import AnnoyIndex
import json
import ast
from ..utils import scrape_link, split_text, get_embeddings, embed_query
from .. import config
from .supa_client import init_supa_client
import openai

INDEX_FILE_NAME = "index.ann"
REBUILD_THRESHOLD = 100  # Adjust this value as needed
added_vectors = 0

import os


async def save_and_load_annoy_index(annoy_index):
    # Check if the index file exists and is not empty
    if not os.path.exists(INDEX_FILE_NAME) or os.path.getsize(INDEX_FILE_NAME) == 0:
        annoy_index.build(10)
        annoy_index.save(INDEX_FILE_NAME)

    # Load the index from the file
    dimension = annoy_index.f
    loaded_index = AnnoyIndex(dimension, "angular")
    loaded_index.load(INDEX_FILE_NAME)
    return loaded_index


async def build_annoy_index():
    client = init_supa_client()
    # global global_annoy_index, global_id_mapping, global_id_mapping_chunk
    # Fetch the vectors from the Supabase 'article_vectors' table
    response, _ = client.table("article_vectors").select("*").execute()
    _, data = response
    vectors = data  # This is a list of dictionaries
    float_vectors = []
    for vector in vectors:
        float_vector = ast.literal_eval(
            vector["embedding"]
        )  # Convert string to list of floats
        float_vectors.append(float_vector)

    # Initialize the Annoy index with the dimension of the vectors
    dimension = len(float_vectors[0])
    annoy_index = AnnoyIndex(
        dimension, "angular"
    )  # Use "angular" for cosine similarity

    # Create a mapping between Annoy IDs (integer) and UUIDs (string)
    id_mapping = {}
    id_mapping_chunk = {}

    # Add the vectors to the Annoy index
    for i, vector in enumerate(vectors):
        float_vector = ast.literal_eval(
            vector["embedding"]
        )  # Convert string to list of floats
        annoy_index.add_item(i, float_vector)
        id_mapping[i] = vector["article"]
        id_mapping_chunk[i] = vector["chunk_index"]

    # Build the index
    annoy_index.build(10)  # Adjust the number of trees for your specific use case

    # Save and load the index
    loaded_index = await save_and_load_annoy_index(annoy_index)

    return loaded_index, id_mapping, id_mapping_chunk


async def upload_article_with_embeddings(
    article, url, annoy_index, id_mapping, id_mapping_chunk
):
    global added_vectors
    client = init_supa_client()
    try:
        article_dict = {
            "title": article.title,
            "meta_description": article.meta_description,
            "url": url,
        }

        # Split the text into chunks and create a JSON object with indices as keys
        text_chunks = split_text(article.cleaned_text)
        chunked_text = {str(i): chunk for i, chunk in enumerate(text_chunks)}
        # add the chunks to the dict
        article_dict["chunks"] = json.dumps(chunked_text)

        # Upload article to Supabase and retrieve the ID
        res, _ = client.table("articles").insert(article_dict).execute()
        _, data = res
        article_id = data[0]["id"]
        # Return newly added embeddings and their Annoy IDs
        new_embeddings = []

        # Generate and store embeddings for the chunks
        for i, chunk in enumerate(text_chunks):
            embedding = get_embeddings(chunk)
            vector_data = {
                "article": article_id,
                "embedding": embedding,
                "chunk_index": i,
            }
            client.table("article_vectors").insert(vector_data).execute()
            # Unload the index before updating it
            annoy_index.unload()

            # Update the Annoy index
            added_vector = add_vector_to_index(
                annoy_index, id_mapping, id_mapping_chunk, vector_data
            )

            added_vectors += 1

            # Save and load the index after updating it
            annoy_index = await save_and_load_annoy_index(annoy_index)
            # Add the new_embedding to the new_embeddings list
            new_embedding = (added_vector, embedding)
            new_embeddings.append(new_embedding)
            if added_vectors >= REBUILD_THRESHOLD:
                # Unload the index before rebuilding it
                annoy_index.unload()

                annoy_index.build(10)  # Rebuild the index
                added_vectors = 0  # Reset the counter

                # Save and load the index after rebuilding it
                annoy_index = await save_and_load_annoy_index(annoy_index)

        return article_id, new_embeddings, annoy_index, id_mapping, id_mapping_chunk
    except Exception as e:
        print(e)
        return e, None


async def update_annoy_index(
    article_id, new_embeddings, annoy_index, id_mapping, id_mapping_chunk
):
    for new_id, new_embedding in new_embeddings:
        annoy_index.add_item(new_id, new_embedding)
        id_mapping[new_id] = article_id
        id_mapping_chunk[new_id] = new_id - len(id_mapping) + 1
    return annoy_index


async def search_similar(query, annoy_index, id_mapping, id_mapping_chunk):
    client = init_supa_client()
    annoy_index.load(INDEX_FILE_NAME)
    query_embedding = await embed_query(query)  # Generate the embedding for the query

    # Find the most similar articles using the Annoy index
    num_results = 3  # Adjust the number of results you want to return
    similar_annoy_ids, distances = annoy_index.get_nns_by_vector(
        query_embedding, num_results, include_distances=True
    )

    result_msg = ""
    # Fetch articles based on the similar article IDs
    for annoy_id, distance in zip(similar_annoy_ids, distances):
        article_id = id_mapping[annoy_id]
        article, _ = client.table("articles").select("*").eq("id", article_id).execute()
        _, data = article
        article_data = data[0]
        # Get the chunk_index and relevant chunk from the 'chunks' field
        chunk_index = id_mapping_chunk[annoy_id]
        chunks = json.loads(article_data["chunks"])
        relevant_chunk = chunks[str(chunk_index)]
        result_dict = {
            "article_data": article_data,
            "relevant_chunk": relevant_chunk,
            "similarity_score": 1 - distance,
        }
        result_msg += f"{article_data['title']} - {article_data['url']}\n{article_data['meta_description']}"
    return result_dict, result_msg


def add_vector_to_index(annoy_index, id_mapping, id_mapping_chunk, vector_data):
    new_id = len(id_mapping)
    float_vector = vector_data["embedding"]
    annoy_index.add_item(new_id, float_vector)
    print("new vector added to index")
    id_mapping[new_id] = vector_data["article"]
    id_mapping_chunk[new_id] = vector_data["chunk_index"]
    print("new id mapping chunk", id_mapping_chunk)
    return new_id  # Add this line to return the new_id
