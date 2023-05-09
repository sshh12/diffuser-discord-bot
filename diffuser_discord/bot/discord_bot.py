from typing import Optional, List
import logging
import time
import os
import re

from discord import app_commands
import asyncio
import discord

from diffuser_discord.bot.image_client import ImageClient, BLANK_IMAGE


SYNC_GUILD = os.environ.get("SYNC_GUILD", None)


class DiscordClient(discord.Client):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        if SYNC_GUILD is not None:
            for guild_id in SYNC_GUILD.split(","):
                guild = discord.Object(id=int(guild_id))
                self.tree.copy_global_to(guild=guild)
                await self.tree.sync(guild=guild)


def _expand_template(template: str) -> List[str]:
    """
    a {photo, painting} of a {dog, cat}
    """
    match = re.search(r"\{([^}]+)\}", template)
    if not match:
        return [template]
    options = match.group(1).split(", ")
    expanded = []
    for option in options:
        expanded += _expand_template(template[: match.start()] + option + template[match.end() :])
    return expanded


class ImagineView(discord.ui.View):
    def __init__(self, prompt: str, user: discord.User, img_client: ImageClient, count: int, seed: Optional[int] = 0):
        super().__init__(timeout=None)
        self.prompt = prompt
        self.user = user
        self.img_client = img_client
        self.seed = seed
        self.count = count

        self.title = f"> {prompt}"
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
        prompts = _expand_template(self.prompt)
        logging.info(f"Generating images for {prompts}")
        img_link = await self.img_client.generate_images(prompts * self.count, self.seed, {})
        self.image_emb.set_image(url=img_link)
        self.seed = hash(time.time())
        self.button.disabled = False
        self.button.label = "🔄"
        await interaction.message.edit(embed=self.image_emb, view=self)


class EnhanceView(discord.ui.View):
    def __init__(
        self,
        prompt: str,
        image_url: str,
        user: discord.User,
        img_client: ImageClient,
        count: int,
        seed: int,
        strength: int,
    ):
        super().__init__(timeout=None)
        self.prompt = prompt
        self.image_url = image_url
        self.user = user
        self.img_client = img_client
        self.seed = seed
        self.strength = strength
        self.count = count

        self.title = f"> {prompt} on {image_url}"
        self.image_emb = discord.Embed()
        self.image_emb.set_image(url=self.image_url)
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
        prompts = _expand_template(self.prompt)
        logging.info(f"Generating image for {prompts} on {self.image_url}")
        img_link = await self.img_client.generate_images_from_image(
            prompts * self.count, self.image_url, self.seed, {"strength": self.strength / 100}
        )
        self.image_emb.set_image(url=img_link)
        self.seed = hash(time.time())
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
        view = ImagineView(prompt=prompt, user=interaction.user, img_client=img_client, seed=seed, count=count)
        await interaction.response.send_message(view.title, embed=view.image_emb, view=view)

    @client.tree.command()
    @app_commands.describe(
        prompt="Caption to enhance the image",
        image_url="The URL to a png/jpg image",
        strength="Indicates how much to transform the reference `image` [0, 100]",
        seed="Random seed for image generation",
    )
    async def enhance(
        interaction: discord.Interaction,
        prompt: str,
        image_url: str,
        strength: Optional[int] = 80,
        seed: Optional[int] = 0,
        count: Optional[int] = 1,
    ):
        view = EnhanceView(
            prompt=prompt,
            image_url=image_url,
            strength=strength,
            user=interaction.user,
            img_client=img_client,
            seed=seed,
            count=count,
        )
        await interaction.response.send_message(view.title, embed=view.image_emb, view=view)


def create_discord_client(img_client: ImageClient) -> discord.Client:
    intents = discord.Intents.default()
    intents.message_content = True
    client = DiscordClient(intents=intents)
    update_discord_client(client, img_client)
    return client
