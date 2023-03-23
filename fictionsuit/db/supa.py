from annoy import AnnoyIndex
import json
import ast
from ..utils import scrape_link, get_embeddings, embed_query
from supabase import create_client
import sys
from .. import config

supabase = None
if config.UPLOAD_DATA_TO_SUPABASE:
    url: str = config.SUPABASE_URL
    key: str = config.SUPABASE_ANON_KEY
    supabase = create_client(url, key)


async def list_first_article():
    global supabase
    response, _ = supabase.table("articles").select("*").execute()
    _, data = response
    return data[0]["title"]


async def build_annoy_index():
    global global_annoy_index, global_id_mapping, global_id_mapping_chunk
    # Fetch the vectors from the Supabase 'article_vectors' table
    response, _ = supabase.table("article_vectors").select("*").execute()
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

    return annoy_index, id_mapping, id_mapping_chunk


async def upload_article_with_embeddings(url):
    global global_annoy_index, global_id_mapping, global_id_mapping_chunk
    supaclient = await supabase()
    try:
        article = await scrape_link(url)
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
        res, _ = supaclient.table("articles").insert(article_dict).execute()
        _, data = res
        article_id = data[0]["id"]
        # Return newly added embeddings and their Annoy IDs
        new_embeddings = []
        # Generate and store embeddings for the chunks
        print("generating embeddings...")
        for i, chunk in enumerate(text_chunks):
            embedding = get_embeddings(chunk)
            vector_data = {
                "article": article_id,
                "embedding": embedding,
                "chunk_index": i,
            }
            print("inserting vector into supa...")
            supaclient.table("article_vectors").insert(vector_data).execute()
            print("creating embeddings result")
            print("global_id_mapping length:", global_id_mapping)
            new_embeddings.append((len(global_id_mapping), embedding))
        # this should return article_id,
        return article_id, new_embeddings
    except Exception as e:
        return e


async def update_annoy_index(article_id, new_embeddings):

    global global_annoy_index, global_id_mapping, global_id_mapping_chunk
    for new_id, new_embedding in new_embeddings:
        global_annoy_index.add_item(new_id, new_embedding)
        global_id_mapping[new_id] = article_id
        global_id_mapping_chunk[new_id] = new_id - len(global_id_mapping) + 1
    return "success"


async def search_similar(query, annoy_index, id_mapping, id_mapping_chunk):
    supaclient = await init_client()
    query_embedding = await embed_query(query)  # Generate the embedding for the query

    # Find the most similar articles using the Annoy index
    num_results = 1  # Adjust the number of results you want to return
    similar_annoy_ids, distances = annoy_index.get_nns_by_vector(
        query_embedding, num_results, include_distances=True
    )

    # Fetch articles based on the similar article IDs
    for annoy_id, distance in zip(similar_annoy_ids, distances):
        article_id = id_mapping[annoy_id]
        article, _ = (
            supaclient.table("articles").select("*").eq("id", article_id).execute()
        )
        _, data = article
        article_data = data[0]
        # Get the chunk_index and relevant chunk from the 'chunks' field
        chunk_index = id_mapping_chunk[annoy_id]
        chunks = json.loads(article_data["chunks"])
        relevant_chunk = chunks[str(chunk_index)]

        result = {
            "article_data": article_data,
            "relevant_chunk": relevant_chunk,
            "similarity_score": 1 - distance,
        }
    return result
