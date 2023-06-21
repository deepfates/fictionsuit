import transformers
from transformers import CLIPTokenizer, CLIPTextModel
import torch
from diffusers import AutoencoderKL, UNet2DConditionModel, PNDMScheduler
from PIL import Image
import pickle
import base64

from ..commands.failure import CommandFailure

torch.backends.cuda.matmul.allow_tf32 = True


class DiffusionModel:
    def __init__(self, model: str):
        self.model_source = model
        self.vae = AutoencoderKL.from_pretrained(
            model, subfolder="vae", torch_dtype=torch.float16
        )
        self.tokenizer = CLIPTokenizer.from_pretrained(
            model, subfolder="tokenizer", torch_dtype=torch.float16
        )
        self.text_encoder = CLIPTextModel.from_pretrained(
            model, subfolder="text_encoder", torch_dtype=torch.float16
        )
        self.unet = UNet2DConditionModel.from_pretrained(
            model, subfolder="unet", torch_dtype=torch.float16
        )
        self.scheduler = PNDMScheduler.from_pretrained(
            model, subfolder="scheduler", torch_dtype=torch.float16
        )
        self.vae.to(device="cuda")
        self.text_encoder.to(device="cuda")
        self.unet.to(device="cuda")
        pass

    def sm_schematize(self):
        return {"schema": "text", "value": f"Diffusion Model `{self.model_source}`"}

    async def sm_default(self, args):
        prompt = [
            "a big fat ugly sea lion great dane hound dog houdini 4k, babaloosa, he's so fucking slimy and wet, glistening sloppy ugly piece of shit seal sea lion orca"
        ]
        antiprompt = [""]
        height = 512
        width = 512
        num_inference_steps = 25
        guidance_scale = 7.5
        # generator = torch.manual_seed(0)
        batch_size = len(prompt)
        positive_tokens = self.tokenizer(
            prompt,
            padding="max_length",
            max_length=self.tokenizer.model_max_length,
            truncation=True,
            return_tensors="pt",
        )
        negative_tokens = self.tokenizer(
            antiprompt,
            padding="max_length",
            max_length=self.tokenizer.model_max_length,
            truncation=True,
            return_tensors="pt",
        )
        with torch.no_grad():
            positive_embeddings = self.text_encoder(
                positive_tokens.input_ids.to(device="cuda")
            )[0]
            negative_embeddings = self.text_encoder(
                negative_tokens.input_ids.to(device="cuda")
            )[0]
            embeddings = torch.cat([negative_embeddings, positive_embeddings], dim=0)

            latents = torch.randn(
                (batch_size, self.unet.in_channels, height // 8, width // 8),
                device="cuda",
                dtype=torch.float16,
            )  # todo: generator

            latents = latents * self.scheduler.init_noise_sigma

            self.scheduler.set_timesteps(num_inference_steps)

            for step in self.scheduler.timesteps:
                latents_expanded = torch.cat([latents] * 2)
                latents_expanded = self.scheduler.scale_model_input(
                    latents_expanded, timestep=step
                )

                noise_prediction = self.unet(
                    latents_expanded, step, encoder_hidden_states=embeddings
                ).sample

                (
                    noise_prediction_negative,
                    noise_prediction_positive,
                ) = noise_prediction.chunk(2)
                noise_prediction = noise_prediction_negative + guidance_scale * (
                    noise_prediction_positive - noise_prediction_negative
                )

                latents = self.scheduler.step(
                    noise_prediction, step, latents
                ).prev_sample
            latents = 1 / 0.18215 * latents
            images = self.vae.decode(latents).sample

            images = (images / 2 + 0.5).clamp(0, 1)
            images = images.detach().cpu().permute(0, 2, 3, 1).numpy()
            images = (images * 255).round().astype("uint8")

            flattened = [image.flatten().tobytes() for image in images]
            base64ed = [base64.b64encode(image).decode("utf-8") for image in flattened]

            return {
                "schema": "image_bytes",
                "height": height,
                "width": width,
                "bytes": base64ed,
            }
            pil_images = [Image.fromarray(image) for image in images]
            for p in pil_images:
                p.save("DIFFUSION_RESULT.png")


class HuggingFaceTextGenerator:
    def __init__(self, model: str):
        self.model = transformers.AutoModelForCausalLM.from_pretrained(
            model,
            trust_remote_code=True,
            low_cpu_mem_usage=True,
            torch_dtype=torch.bfloat16,
        )
        config = transformers.AutoConfig.from_pretrained(model, trust_remote_code=True)
        self.tokenizer = transformers.AutoTokenizer.from_pretrained(
            config.tokenizer_name, low_cpu_mem_usage=True, dtype=torch.bfloat16
        )
        self.model_source = model
        self.tokenizer_source = config.tokenizer_name
        self.model.to(device="cuda")
        self.tokenizer
        self.limit = 100
        self.temperature = 0.8
        self.top_p = 0.945
        self.repetition_penalty = 5.0

    def sm_schematize(self):
        return {"schema": "text", "value": "asdf **q**"}

    async def sm_inspect(self, content):
        return f"### 🤗 Text Generator\n\n**Model** `{self.model_source}`\n\n**Tokenizer** `{self.tokenizer_source}`\n\n**Temperature** `{self.temperature}`\n\n**Top-P** `{self.top_p}`\n\n**Repetition Penalty** `{self.repetition_penalty}`\n\n**Limit** `{self.limit}`"

    async def sm_limit(self, limit):
        try:
            limit = int(limit)
        except:
            return CommandFailure(f"Expected an integer, got {limit}")
        self.limit = limit

    async def sm_temp(self, temperature):
        try:
            temperature = float(temperature)
        except:
            return CommandFailure(f"Expected a number, got {temperature}")
        self.temperature = temperature

    async def sm_top_p(self, top_p):
        try:
            top_p = float(top_p)
        except:
            return CommandFailure(f"Expected a number, got {top_p}")
        self.top_p = top_p

    async def sm_default(self, content):
        return self.tokenizer.decode(
            self.model.generate(
                self.tokenizer(content, return_tensors="pt").input_ids.to("cuda"),
                temperature=self.temperature,
                max_length=self.limit,
                top_p=self.top_p,
                repetition_penalty=self.repetition_penalty,
            )[0],
            skip_special_tokens=True,
        )

    async def sm_raw(self, content):
        return self.model.generate(
            self.tokenizer(content, return_tensors="pt").input_ids.to("cuda"),
            temperature=self.temperature,
            max_length=self.limit,
            top_p=self.top_p,
            repetition_penalty=self.repetition_penalty,
        )[0]
