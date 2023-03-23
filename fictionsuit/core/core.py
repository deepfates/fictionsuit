from ..utils import convert_article, scrape_link, write_md
import openai
from .. import config
from langchain.chat_models import ChatOpenAI
from langchain.text_splitter import CharacterTextSplitter
from langchain.docstore.document import Document
from langchain.chains.summarize import load_summarize_chain
import aiohttp

URL = "https://api.openai.com/v1/chat/completions"

# TODO: extract openai stuff into an openai wrapper
openai_chat = list[dict[str, str]]


def chat_message(role: str, content: str) -> openai_chat:
    return [{"role": role, "content": content}]


async def get_openai_response(messages: openai_chat) -> str:
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {openai.api_key}",
    }

    body = {
        "model": config.OAI_MODEL,
        "temperature": config.TEMPERATURE,
        "max_tokens": config.MAX_TOKENS,
        "messages": messages,
        "top_p": config.TOP_P
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(URL, headers=headers, json=body) as response:
            response_data = await response.json()

    return response_data


# summarize text
async def summarize(url: str):
    try:
        article = await scrape_link(url)
        md_article = convert_article(article, url, "md")
        write_md(md_article, "articles", article.title)
        text = article.cleaned_text
        summary_template = f"""
        {config.SYSTEM_MSG} \n
        {config.SUMMARIZE_MSG} \n 
        """
        summary_template += "{text}"
        llm = ChatOpenAI(temperature=config.TEMPERATURE, max_tokens=config.MAX_TOKENS)
        text_splitter = CharacterTextSplitter()
        texts = text_splitter.split_text(text)
        docs = [Document(page_content=t) for t in texts][:3]
        chain = load_summarize_chain(llm, chain_type="map_reduce")
        result = await chain.arun(docs)
        return result
    except Exception as e:
        print(e)
        return "error, check console"
