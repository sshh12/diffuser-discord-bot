import os

os.environ["FORCE_MEM_EFFICIENT_ATTN"] = "1"

from diffuser_discord.bot import discord_bot, image_client
import logging


def main():
    logging.getLogger().setLevel(logging.DEBUG)
    img_client = image_client.LocalGPUClient(max_image_batch_size=1)
    img_client.init()
    discord_client = discord_bot.create_discord_client(img_client=img_client)
    discord_client.run(os.environ["DISCORD_TOKEN"])


if __name__ == "__main__":
    main()
