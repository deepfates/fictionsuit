from utils import convert_article, scrape_link, write_md, make_stats_str
import openai
import config
from langchain.chat_models import ChatOpenAI
from langchain.text_splitter import CharacterTextSplitter
from langchain.docstore.document import Document
from langchain.chains.summarize import load_summarize_chain
from typing import List, Dict, Sequence
import aiohttp
URL = "https://api.openai.com/v1/chat/completions"
from abc import ABC, abstractmethod
from api_wrap.user_message import UserMessage
from commands.command_group import CommandGroup, command_split

class System(ABC):
    '''A system for handling incoming user messages.'''
    @abstractmethod
    async def enqueue_message(self, message: UserMessage):
        '''Called whenever a new user message arrives.'''
        pass


class BasicCommandSystem(System):
    def __init__(
        self, 
        command_groups: Sequence[CommandGroup], 
        stats_ui=True,
        respond_on_unrecognized=False
        ):
        self.command_groups = command_groups
        self.stats_ui = stats_ui
        self.respond_on_unrecognized = respond_on_unrecognized

        all_commands = [command for group in command_groups for command in group.get_all_commands()]

        if len(all_commands) != len(set(all_commands)):
            # TODO: Print out more useful information, like where the name collision actually is.
            print(f'{"!"*20}\n\nWARNING: MULTIPLE COMMANDS WITH OVERLAPPING COMMAND NAMES\n\n{"!"*20}')
            

    async def enqueue_message(self, message: UserMessage):
        if not message.has_prefix(config.COMMAND_PREFIX):
            return # Not handling non-command messages, for now

        (cmd, args) = command_split(message.content, config.COMMAND_PREFIX)

        if cmd is None:
            return # Nothing but a prefix. Nothing to do.

        for group in self.command_groups:
            if await group.handle(message, cmd, args):
                return

        if cmd == 'help':
            await message.reply(f'Sorry, there\'s no command called "{args}".')
            return

        if self.respond_on_unrecognized:
            await self.direct_chat(message)

    async def direct_chat(self, message: UserMessage):
        messages = chat_message('system', config.SYSTEM_MSG)
        messages += chat_message('user', message.content)
        res = await get_openai_response(messages)
        content = res['choices'][0]['message']['content']
        content = make_stats_str(content, messages, 'chat') if self.stats_ui else content
        await message.reply(content)

def chat_message(role, content):
    return [{'role':role,'content':content}]

async def get_openai_response(messages: List[Dict]) -> str:
    
    headers = {
	"Content-Type": "application/json",
	"Authorization": f"Bearer {openai.api_key}"
    }
    
    body = {
        "model": config.OAI_MODEL,
        "temperature": config.TEMPERATURE,
        "max_tokens": config.MAX_TOKENS,
        "messages": messages
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(URL, headers=headers, json=body) as response:
            response_data = await response.json()

    return response_data

# summarize text
async def summarize(url):
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
