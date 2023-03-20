import os
import openai
import dotenv

dotenv.load_dotenv()

# general
SERVER = os.getenv("SERVER")

# llm
OAI_MODEL = os.getenv("OAI_MODEL", "gpt-3.5-turbo-0301")
openai.api_key = os.getenv("OPENAI_API_KEY")
TEMPERATURE = os.getenv("TEMPERATURE", 1)
MAX_TOKENS = os.getenv("MAX_TOKENS", 500)

# Bot specific
COMMAND_PREFIX = os.getenv("COMMAND_PREFIX", "chat ")
DEV_TOKEN = os.getenv("DISCORD_DEV_TOKEN")
PROD_TOKEN = os.getenv("DISCORD_PROD_TOKEN")

# Prompts
SYSTEM_MSG = os.getenv("SYSTEM_MSG", "You are a helpful assistant. Your responses are ALWAYS 240 characters or less. You never respond over 240 characters.")
SUMMARIZE_MSG = os.getenv("SUMMARIZE_MSG", "Summarize the following text:")