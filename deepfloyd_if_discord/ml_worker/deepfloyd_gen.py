from typing import List

from diffusers import DiffusionPipeline
import torch


class DeepfloydIF:
    def __init__(self):
        self.stage_1 = None
        self.stage_2 = None
        self.stage_3 = None

    def load_weights(self):
        self.stage_1 = DiffusionPipeline.from_pretrained(
            "DeepFloyd/IF-I-XL-v1.0", variant="fp16", torch_dtype=torch.float16
        )
        self.stage_1.enable_model_cpu_offload()
        self.stage_2 = DiffusionPipeline.from_pretrained(
            "DeepFloyd/IF-II-L-v1.0", text_encoder=None, variant="fp16", torch_dtype=torch.float16
        )
        self.stage_2.enable_model_cpu_offload()
        safety_modules = {
            "feature_extractor": self.stage_1.feature_extractor,
            "safety_checker": self.stage_1.safety_checker,
        }
        self.stage_3 = DiffusionPipeline.from_pretrained(
            "stabilityai/stable-diffusion-x4-upscaler", **safety_modules, torch_dtype=torch.float16
        )
        self.stage_3.enable_model_cpu_offload()

    def generate_images(self, prompt: str, nb_images: int, seed: int) -> List["Image"]:
        prompt_embeds, negative_embeds = self.stage_1.encode_prompt([prompt] * nb_images)

        generator = torch.manual_seed(seed)

        images = self.stage_1(
            prompt_embeds=prompt_embeds, negative_prompt_embeds=negative_embeds, generator=generator, output_type="pt"
        ).images

        images = self.stage_2(
            image=images,
            prompt_embeds=prompt_embeds,
            negative_prompt_embeds=negative_embeds,
            generator=generator,
            output_type="pt",
        ).images

        images = self.stage_3(prompt=[prompt] * nb_images, image=images, generator=generator, noise_level=100).images
        return images
