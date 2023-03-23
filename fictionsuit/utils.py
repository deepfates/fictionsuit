import tiktoken
import os
from goose3 import Goose
from . import config
from typing import List, Dict

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


def convert_article(article, url, conversion):
    """
    given a goose3 article object, convert it to a dict or markdown string (more options later maybe)
    """
    print("start convert article")
    converted_article = ""
    if conversion == "dict":
        converted_article = {
            "title": article.title,
            "metadata": article.meta_description,
            "url": url,
            "article_text": article.cleaned_text,
            "featured_image": article.top_image.src,
        }

    elif conversion == "md":
        converted_article = f"""---
title: {article.title}
metadata: {article.meta_description}
url: {url}
featured_image: {article.top_image.src if article.top_image else ""}\n---\n{article.cleaned_text}"""
    else:
        converted_article = "error converting article"
    return converted_article


def write_md(data, doctype, filename):
    """Where doctype is the source/type of resource, e.g. 'articles' or 'tweets' and filename is the name of the file to be saved.
    eg write_md(data, 'articles', 'article.md')
    """
    directory = f"./documents/{doctype}/"

    # Create the directory if it doesn't exist
    if not os.path.exists(directory):
        os.makedirs(directory)

    file_path = os.path.join(directory, filename + ".md")
    with open(file_path, "w") as md_file:
        md_file.write(data)


# given a link to a web article, get its content and metadata
async def scrape_link(link):
    try:
        g = Goose()
        article = g.extract(url=link)
        g.close()
        return article
    except Exception as e:
        print(e)
        return None
