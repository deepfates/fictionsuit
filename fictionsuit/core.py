import openai
import config
import langchain
from langchain import OpenAI, PromptTemplate, LLMChain
from langchain.text_splitter import CharacterTextSplitter
from langchain.chains.mapreduce import MapReduceChain
from langchain.prompts import PromptTemplate
from langchain.docstore.document import Document
from langchain.chains.summarize import load_summarize_chain

def get_openai_response(messages_list):
        try:
            return openai.ChatCompletion.create(
                model=config.OAI_MODEL,
                messages=messages_list,
            )
        except Exception as e:
            print(e)
            return "There has been an error, check console.", {}

# summarize text
async def summarize(text):

    prompt = PromptTemplate(template=config.SYSTEM_MSG+"\n"+config.SUMMARIZE_MSG+" {text}", input_variables=["text"])
    llm = OpenAI(temperature=config.TEMPERATURE, max_tokens=config.MAX_TOKENS)
    text_splitter = CharacterTextSplitter()
    texts = text_splitter.split_text(text)
    docs = [Document(page_content=t) for t in texts][:3]
    chain = load_summarize_chain(llm, chain_type="map_reduce", map_prompt=prompt)
    return chain.run(docs)