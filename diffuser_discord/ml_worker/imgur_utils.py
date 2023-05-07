import requests
import logging
import base64
import io
import os

IMGUR_CLIENT_ID = os.environ.get("IMGUR_CLIENT_ID", "")


def upload_to_imgur(pil_image) -> str:
    img_bytes = io.BytesIO()
    pil_image.save(img_bytes, format="PNG")
    resp = requests.post(
        "https://api.imgur.com/3/image",
        headers={"Authorization": f"Client-ID {IMGUR_CLIENT_ID}"},
        data={
            "image": base64.b64encode(img_bytes.getvalue()),
            "type": "base64",
            "name": "img",
            "title": "img",
        },
    ).json()
    logging.info("Imgur upload " + repr(resp))
    return resp["data"]["link"]
