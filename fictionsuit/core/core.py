from langchain.chains.summarize import load_summarize_chain
from langchain.chat_models import ChatOpenAI
from langchain.docstore.document import Document
from langchain.text_splitter import CharacterTextSplitter

from .. import config
from ..utils import convert_article, scrape_link, write_md


# summarize text
async def summarize(url: str):
    try:
        article = await scrape_link(url)
        # md_article = convert_article(article, url, "md")
        # write_md(md_article, "articles", article.title)
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
