from typing import List, Optional, Tuple
from PIL import Image
import requests
import math
import io


def _get_grid_shape(n: int) -> Tuple[int, int]:
    if n == 1:
        return (1, 1)
    else:
        rows = int(math.ceil(math.sqrt(n)))
        cols = int(math.ceil(n / float(rows)))
        return (rows, cols)


def image_grid(imgs: List["Image"], shape: Optional[Tuple] = None) -> "Image":
    if shape is not None:
        cols, rows = shape
    else:
        cols, rows = _get_grid_shape(len(imgs))

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
