import tiktoken
import config
import goose3

# will likely change w api update
# https://platform.openai.com/docs/guides/chat/managing-tokens
def num_tokens_from_messages(messages, model=config.OA_MODEL):
    """Returns the number of tokens used by a list of messages."""
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        encoding = tiktoken.get_encoding("cl100k_base")

    if model == "gpt-3.5-turbo-0301":  # note: future models may deviate from this
        num_tokens = 0
        for message in messages:

            num_tokens += (
                4  # every message follows <im_start>{role/name}\n{content}<im_end>\n
            )
            for key, value in message.items():
                num_tokens += len(encoding.encode(value))
                if key == "name":  # if there's a name, the role is omitted
                    num_tokens += -1  # role is always required and always 1 token
        num_tokens += 2  # every reply is primed with <im_start>assistant
        return num_tokens
    else:
        raise NotImplementedError(
            f"""num_tokens_from_messages() is not presently implemented for model {model}.
    See https://github.com/openai/openai-python/blob/main/chatml.md for information on how messages are converted to tokens."""
        )


# TODO pass in vars whether this is gpt-4 or 3.5 for cost and max tokens
def make_stats_str(content, messages, mode):
    tokens = num_tokens_from_messages(messages)
    hr = "-~-~-~-~-~"
    token_str = f"approx {tokens} tokens ({tokens/4096*100:.2f}% of max)"
    messages_str = f"{len(messages)} messages in memory"
    return f"{content}\n{hr}\n{token_str} / {messages_str} / mode: {mode}"

async def send_long_message(channel, message):
    '''Sends a message to a Discord channel, splitting it into chunks if it's too long.'''
    if len(message) < 2000:
        await channel.send(message)
    else:
        chunks = [message[i:i+2000] for i in range(0, len(message), 2000)]
        for chunk in chunks:
            await channel.send(chunk)
# read a url
def read_url(url):
    g = goose3.Goose()
    article = g.extract(url=url)
    return article.cleaned_text

# split text into chunks of specified length
def split_text(text, length=1000):
    chunks = []
    while len(text) > length:
        chunk = text[:length]
        chunks.append(chunk)
        text = text[length:]
    chunks.append(text)
    print(chunks)
    return chunks
