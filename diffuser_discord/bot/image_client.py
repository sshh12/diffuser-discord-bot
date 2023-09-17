from typing import Optional, Dict, List
from abc import ABC, abstractmethod
from concurrent.futures import ProcessPoolExecutor
import asyncio
import logging
import modal


ERROR_IMAGE = "https://i.imgur.com/CJ7DFk3.png"
BLANK_IMAGE = "https://i.imgur.com/HdKWBzA.png"


class ImageClient(ABC):
    @abstractmethod
    def init(self):
        pass

    @abstractmethod
    async def generate_images(self, prompts: List[str], seed: int, hparams: Dict) -> str:
        pass

    @abstractmethod
    async def generate_images_from_image(self, prompts: List[str], image_url: str, seed: int, hparams: Dict) -> str:
        pass


def _local_init():
    global deep_floyd
    from diffuser_discord.ml_worker import deepfloyd_gen

    deep_floyd = deepfloyd_gen.DeepFloydIF()
    deep_floyd.load_weights()


def _local_generate_images(prompts: List[str], seed: int, batch_size: int, hparams: Dict) -> str:
    global deep_floyd
    from diffuser_discord.ml_worker import imgur_utils, image_utils

    try:
        img_list = []
        for i in range(0, len(prompts), batch_size):
            prompt_chunk = prompts[i : i + batch_size]
            img_list.extend(deep_floyd.generate_images(prompt_chunk, seed=seed + i, hparams=hparams))
        img = image_utils.image_grid(img_list)
        return imgur_utils.upload_to_imgur(img)
    except Exception as e:
        logging.error(e)
    return ERROR_IMAGE


def _local_generate_images_from_image(
    prompts: List[str], image_url: str, seed: int, batch_size: int, hparams: Dict
) -> str:
    global deep_floyd
    from diffuser_discord.ml_worker import imgur_utils, image_utils

    original_image = image_utils.image_from_url(image_url)
    original_image = original_image.resize((512, 512))

    try:
        img_list = []
        for i in range(0, len(prompts), batch_size):
            prompt_chunk = prompts[i : i + batch_size]
            img_list.extend(
                deep_floyd.generate_images_from_image(
                    prompt_chunk, [original_image] * len(prompt_chunk), seed=seed + i, hparams=hparams
                )
            )
            # HACK: Handle OOM from img2img
            deep_floyd.reload_weights()
        img = image_utils.image_grid(img_list)
        return imgur_utils.upload_to_imgur(img)
    except Exception as e:
        logging.error(e)
    return ERROR_IMAGE


class LocalGPUClient(ImageClient):
    def __init__(
        self, max_batch_size: Optional[int] = 4, max_image_batch_size: Optional[int] = 4, max_workers: Optional[int] = 1
    ) -> None:
        self.max_batch_size = max_batch_size
        self.max_image_batch_size = max_image_batch_size
        self.max_workers = max_workers
        self.executor = None

    def init(self):
        self.executor = ProcessPoolExecutor(max_workers=self.max_workers, initializer=_local_init)

    async def generate_images(self, prompts: List[str], seed: int, hparams: Dict) -> str:
        loop = asyncio.get_event_loop()
        output_link = await loop.run_in_executor(
            self.executor, _local_generate_images, prompts, seed, self.max_batch_size, hparams
        )
        return output_link

    async def generate_images_from_image(self, prompts: List[str], image_url: str, seed: int, hparams: Dict) -> str:
        loop = asyncio.get_event_loop()
        output_link = await loop.run_in_executor(
            self.executor,
            _local_generate_images_from_image,
            prompts,
            image_url,
            seed,
            self.max_image_batch_size,
            hparams,
        )
        return output_link


class ModalClient(ImageClient):
    MAX_BATCH_SIZE = 9

    def __init__(self) -> None:
        pass

    def init(self):
        self.generate_images_func = modal.Function.lookup("diffuser-discord-bot", "generate_images")

    async def generate_images(self, prompts: List[str], seed: int, hparams: Dict) -> str:
        # arbitrary cap
        if len(prompts) > ModalClient.MAX_BATCH_SIZE:
            prompts = prompts[: ModalClient.MAX_BATCH_SIZE]
        out_url = await self.generate_images_func.remote.aio(
            prompts,
            seed,
            hparams.get("steps", 50),
            hparams.get("high_noise_frac", 0.8),
            hparams.get("negative_prompt", 0.8),
        )
        return out_url

    async def generate_images_from_image(self, prompts: List[str], image_url: str, seed: int, hparams: Dict) -> str:
        raise NotImplementedError("ModalClient does not support image generation from image")
