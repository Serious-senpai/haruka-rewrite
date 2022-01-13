import discord

from core import bot


json = {
    "name": "rr",
    "type": 1,
    "description": "Send a rickroll video",
}


@bot.slash(json)
async def _rr_slash(interaction: discord.Interaction):
    await interaction.response.defer()
    await interaction.followup.send(file=discord.File("./bot/assets/misc/video0.mp4"))
