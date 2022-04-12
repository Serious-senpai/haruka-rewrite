from typing import Literal

import discord
from discord import app_commands

from _types import Interaction
from core import bot


async def create_image_slash_command() -> None:
    await bot.image.wait_until_ready()

    sfw_keys = sorted(bot.image.sfw.keys())
    nsfw_keys = sorted(bot.image.nsfw.keys())

    sfw_choices = [app_commands.Choice(name=sfw_keys[i], value=i) for i in range(len(sfw_keys))]
    nsfw_choices = [app_commands.Choice(name=nsfw_keys[i], value=i) for i in range(len(nsfw_keys))]

    class _ImageSlashCommand(app_commands.Group):
        @app_commands.command(name="sfw", description="Get a random SFW image")
        @app_commands.describe(category="The image category")
        @app_commands.choices(category=sfw_choices[:25])  # Discord limit
        async def _sfw_slash(self, interaction: Interaction, category: app_commands.Choice[int]):
            await self._process_request(interaction, "sfw", category.name)

        @app_commands.command(name="nsfw", description="Get a random NSFW image")
        @app_commands.describe(category="The image category")
        @app_commands.choices(category=nsfw_choices[:25])  # Discord limit
        async def _nsfw_slash(self, interaction: Interaction, category: app_commands.Choice[int]):
            try:
                if not interaction.channel.is_nsfw():
                    return await interaction.response.send_message("🔞 This command can only be invoked in a NSFW channel.")
            except AttributeError:
                return await interaction.response.send_message("Cannot process the command in this channel!")

            await self._process_request(interaction, "nsfw", category.name)

        async def _process_request(self, interaction: Interaction, mode: Literal["sfw", "nsfw"], category: str) -> None:
            await interaction.response.defer()
            image_url = await bot.image.get(category, mode=mode)
            if image_url is None:
                return await interaction.followup.send("Cannot fetch any images from this category right now...")

            embed = discord.Embed()
            embed.set_image(url=image_url)
            embed.set_author(
                name="This is your image!",
                icon_url=bot.user.avatar.url,
            )
            await interaction.followup.send(embed=embed)

    bot.tree.add_command(_ImageSlashCommand(name="image", description="Get a random anime image"))


bot._create_image_slash_command = create_image_slash_command()
