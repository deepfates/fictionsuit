import tiktoken
from langchain.text_splitter import CharacterTextSplitter
import os
from goose3 import Goose
from . import config
from typing import List, Dict
import openai


# will likely change w api update
# https://platform.openai.com/docs/guides/chat/managing-tokens
def num_tokens_from_messages(
    messages: List[Dict], model: str = config.OAI_MODEL
) -> int:
    """Returns the number of tokens used by a list of messages."""
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        encoding = tiktoken.get_encoding("cl100k_base")

    if model == "gpt-3.5-turbo-0301":  # note: future models may deviate from this
        num_tokens = 0
        for message in messages:
            num_tokens += (
                4  # every message follows <im_start>{role/name}\n{content}<im_end>\n
            )
            for key, value in message.items():
                num_tokens += len(encoding.encode(value))
                if key == "name":  # if there's a name, the role is omitted
                    num_tokens += -1  # role is always required and always 1 token
        num_tokens += 2  # every reply is primed with <im_start>assistant
        return num_tokens
    else:
        raise NotImplementedError(
            f"""num_tokens_from_messages() is not presently implemented for model {model}.
    See https://github.com/openai/openai-python/blob/main/chatml.md for information on how messages are converted to tokens."""
        )


# TODO pass in vars whether this is gpt-4 or 3.5 for cost and max tokens
def make_stats_str(content: str, messages: List[Dict], mode: str) -> str:
    tokens = num_tokens_from_messages(messages)
    hr = "-~-~-~-~-~"
    token_str = f"approx {tokens} tokens ({tokens/4096*100:.2f}% of max)"
    messages_str = f"{len(messages)} messages in memory"
    return f"{content}\n{hr}\n{token_str} / {messages_str} / mode: {mode}"


def convert_document(document, url, conversion):
    """
    given a goose3 document object, convert it to a dict or markdown string (more options later maybe)
    """
    converted_document = ""
    if conversion == "dict":
        converted_document = {
            "title": document.title,
            "metadata": document.meta_description,
            "url": url,
            "document_text": document.cleaned_text,
            "featured_image": document.top_image.src,
        }

    elif conversion == "md":
        converted_document = f"""---
title: {document.title}
metadata: {document.meta_description}
url: {url}
featured_image: {document.top_image.src if document.top_image else ""}\n---\n{document.cleaned_text}"""
    else:
        converted_document = "error converting document"
    return converted_document


def write_md(data, doctype, filename):
    """Where doctype is the source/type of resource, e.g. 'documents' or 'tweets' and filename is the name of the file to be saved.
    eg write_md(data, 'documents', 'document.md')
    """
    directory = f"./documents/{doctype}/"

    # Create the directory if it doesn't exist
    if not os.path.exists(directory):
        os.makedirs(directory)

    file_path = os.path.join(directory, filename + ".md")
    with open(file_path, "w") as md_file:
        md_file.write(data)


# given a link to a web document, get its content and metadata
async def scrape_link(link):
    try:
        g = Goose()
        document = g.extract(url=link)
        g.close()
        return document
    except Exception as e:
        print(e)
        return None


def split_text(text):
    text_splitter = (
        CharacterTextSplitter()
    )  # could consider using TokenTextSplitter instead
    texts = text_splitter.split_text(text)
    return texts


def get_embeddings(text):
    response = openai.Embedding.create(
        model="text-embedding-ada-002",
        encoding="cl100k_base",
        input=text,
        max_tokens=8191,
    )
    embeddings = response["data"][0]["embedding"]
    return embeddings
