from typing import Any

import discord
from discord import app_commands

from _types import Interaction
from core import bot
from lib import saucenao


class _SauceSlashCommand(app_commands.Group):
    @app_commands.command(name="image", description="Upload an artwork and find its source")
    @app_commands.describe(attachment="The artwork to find the source of")
    async def _image_slash(self, interaction: Interaction, attachment: discord.Attachment):
        await self._process_request(interaction, attachment.url)

    @app_commands.command(name="url", description="Find the artwork source from its URL")
    @app_commands.describe(url="The image URL")
    async def _url_slash(self, interaction: Interaction, url: str):
        await self._process_request(interaction, url)

    async def _process_request(self, interaction: Interaction, image_url: str) -> Any:
        await interaction.response.defer()
        results = await saucenao.SauceResult.get_sauce(image_url, session=interaction.client.session)
        if not results:
            return await interaction.followup.send("Cannot find the image sauce.")

        embed = results[0].create_embed()
        embed.set_author(
            name="Image search result",
            icon_url=interaction.client.user.avatar.url,
        )
        embed.set_footer(text="For all results, consider using the text command")
        await interaction.followup.send(embed=embed)


group = _SauceSlashCommand(name="sauce", description="Find the source of an artwork")
bot.tree.add_command(group)
if bot.side_client:
    bot.side_client.tree.add_command(group)
