import os

import dotenv
import openai

dotenv.load_dotenv()

# general
SERVER = os.getenv("SERVER")

# llm
OAI_MODEL = os.getenv("OAI_MODEL", "gpt-3.5-turbo-0301")
openai.api_key = os.getenv("OPENAI_API_KEY")
TEMPERATURE = float(os.getenv("TEMPERATURE", 1.3))
TOP_P = float(os.getenv("TOP_P", 1))
MAX_TOKENS = int(os.getenv("MAX_TOKENS", 500))

# Bot specific
COMMAND_PREFIX = os.getenv("COMMAND_PREFIX", "chat ")
DEV_TOKEN = os.getenv("DISCORD_DEV_TOKEN")
PROD_TOKEN = os.getenv("DISCORD_PROD_TOKEN")

# Prompts
SYSTEM_MSG = os.getenv(
    "SYSTEM_MSG",
    "You are a helpful assistant. Your responses are ALWAYS 240 characters or less. You never respond over 240 characters.",
)
SUMMARIZE_MSG = os.getenv("SUMMARIZE_MSG", "Summarize the following text:")

# Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY")
UPLOAD_TO_SUPABASE = True

# Embedding globals
embeddings_cache = {"embeddings_list": [], "id_mappings": [], "needs_update": True}

# Bluesky social
BSKY_USERNAME = os.getenv("BSKY_USERNAME")
BSKY_PASSWORD = os.getenv("BSKY_PASSWORD")
