import os
import openai
import dotenv

dotenv.load_dotenv()

DEV_TOKEN = os.environ["DISCORD_DEV_TOKEN"]
PROD_TOKEN = os.environ["DISCORD_PROD_TOKEN"]
SERVER = os.environ["SERVER"]
OA_MODEL = "gpt-3.5-turbo-0301"
openai.api_key = os.environ["OPENAI_API_KEY"]

COMMAND_PREFIX = os.environ["COMMAND_PREFIX"] if "COMMAND_PREFIX" in os.environ else "chat "