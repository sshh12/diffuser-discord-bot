from typing import Optional, Dict
from abc import ABC, abstractmethod
from concurrent.futures import ProcessPoolExecutor
import asyncio
import logging

ERROR_IMAGE = "https://i.imgur.com/CJ7DFk3.png"


class ImageClient(ABC):
    @abstractmethod
    def init(self):
        pass

    @abstractmethod
    async def generate_images(self, prompt: str, seed: int, nb_images: int, hparams: Dict) -> str:
        pass

    @abstractmethod
    async def generate_images_from_image(
        self, prompt: str, image_url: str, seed: int, nb_images: int, hparams: Dict
    ) -> str:
        pass


def _local_init():
    global deep_floyd
    from deepfloyd_if_discord.ml_worker import deepfloyd_gen

    deep_floyd = deepfloyd_gen.DeepFloydIF()
    deep_floyd.load_weights()


def _local_generate_images(prompt: str, seed: int, nb_images: int, hparams: Dict) -> str:
    global deep_floyd
    from deepfloyd_if_discord.ml_worker import imgur_utils, image_utils

    try:
        imgs = deep_floyd.generate_images([prompt] * nb_images, seed=seed, hparams=hparams)
        img = image_utils.image_grid(imgs, 2, (len(imgs) + 1) // 2)
        return imgur_utils.upload_to_imgur(img)
    except Exception as e:
        logging.error(e)
    return ERROR_IMAGE


def _local_generate_images_from_image(prompt: str, image_url: str, seed: int, nb_images: int, hparams: Dict) -> str:
    global deep_floyd
    from deepfloyd_if_discord.ml_worker import imgur_utils, image_utils

    original_image = image_utils.image_from_url(image_url)
    original_image = original_image.resize((512, 512))

    try:
        imgs = deep_floyd.generate_images_from_image(
            [prompt] * nb_images, [original_image] * nb_images, seed=seed, hparams=hparams
        )
        # HACK: Handle OOM from img2img
        deep_floyd.reload_weights()
        img = image_utils.image_grid(imgs, 2, (len(imgs) + 1) // 2)
        return imgur_utils.upload_to_imgur(img)
    except Exception as e:
        logging.error(e)
    return ERROR_IMAGE


class LocalGPUClient:
    def __init__(
        self, max_batch_size: Optional[int] = 4, max_image_batch_size: Optional[int] = 1, max_workers: Optional[int] = 1
    ) -> None:
        self.max_batch_size = max_batch_size
        self.max_image_batch_size = max_image_batch_size
        self.max_workers = max_workers
        self.executor = None

    def init(self):
        self.executor = ProcessPoolExecutor(max_workers=self.max_workers, initializer=_local_init)

    async def generate_images(self, prompt: str, seed: int, nb_images: int, hparams: Dict) -> str:
        loop = asyncio.get_event_loop()
        nb_images = min(self.max_batch_size, nb_images)
        output_link = await loop.run_in_executor(
            self.executor, _local_generate_images, prompt, seed, nb_images, hparams
        )
        return output_link

    async def generate_images_from_image(
        self, prompt: str, image_url: str, seed: int, nb_images: int, hparams: Dict
    ) -> str:
        loop = asyncio.get_event_loop()
        nb_images = min(self.max_image_batch_size, nb_images)
        output_link = await loop.run_in_executor(
            self.executor, _local_generate_images_from_image, prompt, image_url, seed, nb_images, hparams
        )
        return output_link
