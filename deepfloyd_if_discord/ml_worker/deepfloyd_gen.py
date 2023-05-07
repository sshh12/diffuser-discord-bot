from typing import List, Dict
import gc

from diffusers import DiffusionPipeline, IFImg2ImgPipeline, IFImg2ImgSuperResolutionPipeline, IFSuperResolutionPipeline
import torch


class DeepFloydIF:
    def __init__(self):
        self.stage_1 = None
        self.stage_2 = None
        self.stage_3 = None
        self.stage_1_img2img = None
        self.stage_2_img2img = None

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

        self.stage_1_img2img = IFImg2ImgPipeline(**self.stage_1.components)
        self.stage_2_img2img = IFImg2ImgSuperResolutionPipeline(**self.stage_2.components)

    def reload_weights(self):
        del self.stage_1
        del self.stage_2
        del self.stage_3
        del self.stage_1_img2img
        del self.stage_2_img2img
        gc.collect()
        torch.cuda.empty_cache()
        self.load_weights()

    def generate_images(self, prompts: List[str], seed: int, hparams: Dict) -> List["Image"]:
        generator = torch.manual_seed(seed)
        prompt_embeds, negative_embeds = self.stage_1.encode_prompt(prompts)

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

        images = self.stage_3(prompt=prompts, image=images, generator=generator, noise_level=100).images
        return images

    def generate_images_from_image(
        self, prompts: List[str], original_images: List["Image"], seed: int, hparams: Dict
    ) -> List["Image"]:
        generator = torch.manual_seed(seed)
        prompt_embeds, negative_embeds = self.stage_1_img2img.encode_prompt(prompts)

        strength = hparams.get("strength")

        images = self.stage_1_img2img(
            image=original_images,
            prompt_embeds=prompt_embeds,
            negative_prompt_embeds=negative_embeds,
            generator=generator,
            output_type="pt",
            strength=strength,
        ).images

        images = self.stage_2_img2img(
            image=images,
            original_image=original_images,
            prompt_embeds=prompt_embeds,
            negative_prompt_embeds=negative_embeds,
            generator=generator,
            output_type="pt",
            strength=strength,
        ).images

        images = self.stage_3(prompt=prompts, image=images, generator=generator, noise_level=100).images

        return images
