import os
import transformers
import torch

from ..api_wrap.huggingface import HuggingFaceTextGenerator, DiffusionModel

from ..core.user_message import UserMessage
from .command_group import CommandGroup


# TODO rename
class MPT(CommandGroup):
    def __init__(self):
        pass

    async def cmd_hf_diffuser(self, message: UserMessage, args: str):
        """TODO: doc"""
        if args == "":
            args = "ql/hf-diff/sd2-base"
        path = f"/run/media/johnim/ssd0/ml_models/{args}"
        if os.path.exists(path):
            return DiffusionModel(model=path)
        return DiffusionModel(model=args)

    async def cmd_hf_lm(self, message: UserMessage, args: str):
        """Load a language model from HuggingFace transformers.
        (Using AutoModelForCausalLM and AutoTokenizer)
        Usage:
        `hf_lm mpt/7b`"""
        if args == "":
            args = "mpt/7b"
        path = f"/run/media/johnim/ssd0/ml_models/{args}"
        if os.path.exists(path):
            return HuggingFaceTextGenerator(model=path)
        return HuggingFaceTextGenerator(model=args)

    async def cmd_hf_localize_lm(self, message: UserMessage, args: str):
        """Download the model, convert to bfloat16, and save it locally.
        Usage:
        `localize mosaicml/mpt-7b-storywriter as mpt/7b-storywriter`"""
        arg_split = args.split("as")
        model_name = arg_split[0].rstrip()
        if len(arg_split) < 2:
            path = model_name
        else:
            path = arg_split[1].lstrip()
        path = f"/run/media/johnim/ssd0/ml_models/{path}"
        model = transformers.AutoModelForCausalLM.from_pretrained(
            model_name,
            trust_remote_code=True,
            low_cpu_mem_usage=True,
            torch_dtype=torch.bfloat16,
        )
        model.save_pretrained(path)
