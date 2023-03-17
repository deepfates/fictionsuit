import openai
import config
import prompts
from utils import make_stats_str


class Bot:
    def __init__(
        self,
        system_msg=prompts.SYSTEM_MSG,
        stats_ui=True,
        command_prefix=prompts.COMMAND_PREFIX,
        mode="conversation",
    ):
        self.system_msg = system_msg
        self.messages = [{"role": "system", "content": system_msg}]
        self.stats_ui = stats_ui
        self.command_prefix = command_prefix
        self.mode = mode

    def toggle_stats_ui(self, content, messages):
        if self.stats_ui:
            str = make_stats_str(content, messages, self.mode)
            return str
        else:
            return content

    def respond(self, message):  # main entryway for bot
        message = " ".join(message.split(" ")[1:])
        self.messages.append({"role": "user", "content": message})
        if message.startswith("help"):
            pass
            # update self.messages
        if message.startswith("read"):
            self.mode = "read"
            content = "i was just told to read"
            # TODO add summarize code here
            # update self.messages
        else:
            self.mode = "conversation"
            res = self.get_openai_response(self.messages)
            content = res["choices"][0]["message"]["content"]
            self.messages.append({"role": "assistant", "content": content})
            # update self.messages
        return self.toggle_stats_ui(content, self.messages)

    def get_openai_response(self, messages_list):
        try:
            return openai.ChatCompletion.create(
                model=config.OA_MODEL,
                messages=messages_list,
            )
        except Exception as e:
            print(e)
            return "There has been an error, check console.", {}
