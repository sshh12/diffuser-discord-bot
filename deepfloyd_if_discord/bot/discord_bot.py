from typing import Optional
import os
import logging

from discord import app_commands
import asyncio
import discord

from deepfloyd_if_discord.bot.image_client import ImageClient

SYNC_GUILD = os.environ.get("SYNC_GUILD", None)
BLANK_IMAGE = "https://i.imgur.com/HdKWBzA.png"


class DiscordClient(discord.Client):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        if SYNC_GUILD is not None:
            guild = discord.Object(id=int(SYNC_GUILD))
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)


class ImageView(discord.ui.View):
    def __init__(
        self, prompt: str, user: discord.User, img_client: ImageClient, nb_images: int, seed: Optional[int] = 0
    ):
        super().__init__(timeout=None)
        self.prompt = prompt
        self.user = user
        self.img_client = img_client
        self.seed = seed
        self.nb_images = nb_images

        self.title = f"{prompt} (x{nb_images})"
        self.image_emb = discord.Embed()
        self.image_emb.set_image(url=BLANK_IMAGE)
        self.generate_image_task = None
        self.button = None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user == self.user

    @discord.ui.button(label="Start", custom_id="start", style=discord.ButtonStyle.primary)
    async def on_start(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.button = button
        self.button.disabled = True
        self.button.label = "Loading..."
        await interaction.response.edit_message(view=self)

        self.generate_image_task = asyncio.create_task(self.generate_image(interaction))

    async def generate_image(self, interaction: discord.Interaction):
        logging.info(f"Generating image for {self.prompt}")
        img_link = await self.img_client.generate_images(self.prompt, self.seed, self.nb_images)
        self.image_emb.set_image(url=img_link)
        self.seed += 1
        self.button.disabled = False
        self.button.label = "🔄"
        await interaction.message.edit(embed=self.image_emb, view=self)


def update_discord_client(client: discord.Client, img_client: ImageClient):
    @client.event
    async def on_ready():
        logging.info(f"We have logged in as {client.user}")

    @client.tree.command()
    @app_commands.describe(prompt="Caption to generate an image for", seed="Random seed for image generation")
    async def imagine(interaction: discord.Interaction, prompt: str, seed: Optional[int] = 0, count: Optional[int] = 1):
        view = ImageView(prompt=prompt, user=interaction.user, img_client=img_client, seed=seed, nb_images=count)
        await interaction.response.send_message(view.title, embed=view.image_emb, view=view)


def create_discord_client(img_client: ImageClient) -> discord.Client:
    intents = discord.Intents.default()
    intents.message_content = True
    client = DiscordClient(intents=intents)
    update_discord_client(client, img_client)
    return client
