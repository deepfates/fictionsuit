import config
from langchain.prompts.prompt import PromptTemplate
from langchain.chains import LLMChain
from langchain.chat_models import ChatOpenAI
from langchain.prompts.chat import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    SystemMessagePromptTemplate,
    AIMessagePromptTemplate
)
chat = ChatOpenAI(temperature=config.TEMP)

# The system prompt can be enhanced by re-inserting it at the end of the message list
# This may also help with prompt injection techniques
system_prompt = SystemMessagePromptTemplate.from_template(config.SYSTEM_MSG)
character_prompt = HumanMessagePromptTemplate.from_template(f"""Here are my instructions: "{config.SYSTEM_MSG}". Now respond to my previous message in character.""")

# Prompt templates can take one or more input variables and chain the LLM call to fill them in
reply_prompt = HumanMessagePromptTemplate(
        prompt=PromptTemplate(
            template="{message}",
            input_variables=["message"],
        )
    )
reply_prompt_template = ChatPromptTemplate.from_messages([system_prompt, reply_prompt, character_prompt])
reply_chain = LLMChain(llm=chat, prompt=reply_prompt_template )


if __name__ == "__main__":
    print(reply_chain.run("Report status"))