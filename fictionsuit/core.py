import openai
from utils import split_text
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
    # chunks = split_text(text)
    # summaries = []
    # prompt = []
    # prompt.append({"role": "system", "content": prompts.SYSTEM_MSG})
    # prompt.append({"role": "user", "content": prompts.SUMMARIZE_MSG})
    # for chunk in chunks:
    #     prompt.append({"role": "user", "content": chunk})
    #     summaries.append(
    #         openai.ChatCompletion.create(
    #             model=config.OAI_MODEL, messages=prompt, max_tokens=100
    #         )["choices"][0]["message"]["content"]
    #     )
    #     # print(summaries)
    #     prompt.pop()
    prompt = PromptTemplate(template=config.SYSTEM_MSG+config.SUMMARIZE_MSG, input_variables=["text"])
    llm = OpenAI(temperature=1.3)
    text_splitter = CharacterTextSplitter()
    texts = text_splitter.split_text(text)
    docs = [Document(page_content=t) for t in texts][:3]
    chain = load_summarize_chain(llm, chain_type="map_reduce", map_prompt=prompt)
    return chain.run(docs)
    

    # return "\n".join(summaries)