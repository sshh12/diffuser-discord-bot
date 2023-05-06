from typing import Optional
from abc import ABC, abstractmethod
from concurrent.futures import ProcessPoolExecutor
import asyncio


class ImageClient(ABC):
    @abstractmethod
    def init(self):
        pass

    @abstractmethod
    async def generate_images(self, prompt: str, seed: int, nb_images: int) -> str:
        pass


def _local_init():
    global floyd
    from deepfloyd_if_discord.ml_worker import deepfloyd_gen

    floyd = deepfloyd_gen.DeepfloydIF()
    floyd.load_weights()


def _local_generate_images(prompt: str, seed: int, nb_images: int) -> str:
    global floyd
    from deepfloyd_if_discord.ml_worker import imgur_utils, image_utils

    imgs = floyd.generate_images(prompt, nb_images=nb_images, seed=seed)

    if len(imgs) == 1:
        img = imgs[0]
    else:
        img = image_utils.image_grid(imgs, 2, (len(imgs) + 1) // 2)

    link = imgur_utils.upload_to_imgur(img)
    return link


class LocalGPUClient:
    def __init__(self, max_batch_size: Optional[int] = 4) -> None:
        self.max_batch_size = max_batch_size

    def init(self):
        self.executor = ProcessPoolExecutor(max_workers=1, initializer=_local_init)

    async def generate_images(self, prompt: str, seed: int, nb_images: int) -> str:
        loop = asyncio.get_event_loop()
        nb_images = min(self.max_batch_size, nb_images)
        output_link = await loop.run_in_executor(self.executor, _local_generate_images, prompt, seed, nb_images)
        return output_link
