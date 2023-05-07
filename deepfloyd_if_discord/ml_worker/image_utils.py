from typing import List
from PIL import Image
import requests
import io


def image_grid(imgs: List["Image"], rows: int, cols: int) -> "Image":
    grid = imgs[0]
    if len(imgs) > 1:
        w, h = imgs[0].size
        grid = Image.new("RGB", size=(cols * w, rows * h))

        for i, img in enumerate(imgs):
            grid.paste(img, box=(i % cols * w, i // cols * h))
    return grid


def image_from_url(url: str) -> "Image":
    try:
        resp = requests.get(url)
    except:
        # basic retry
        resp = requests.get(url)
    img = Image.open(io.BytesIO(resp.content))
    img = img.convert("RGB")
    return img
