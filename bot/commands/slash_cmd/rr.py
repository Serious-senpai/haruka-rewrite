import discord

from _types import Interaction
from core import bot


@bot.slash(
    name="rr",
    description="Send a rickroll video"
)
async def _rr_slash(interaction: Interaction):
    await interaction.response.defer()
    await interaction.followup.send(file=discord.File("./bot/assets/misc/video0.mp4"))
