import asyncio

from discord import app_commands

from _types import Interaction
from core import bot


@bot.slash(
    name="skip",
    description="Skip the playing song",
    official_client=False,
)
@app_commands.guild_only()
async def _skip_slash(interaction: Interaction):
    await interaction.response.defer()
    player = interaction.guild.voice_client

    if player:
        asyncio.create_task(player.skip())
        await interaction.followup.send("Skipped.")

    else:
        await interaction.followup.send("No currently connected player.")
