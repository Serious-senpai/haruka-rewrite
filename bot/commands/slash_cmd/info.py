import discord
from discord import app_commands

from _types import Interaction
from core import bot
from lib import info


@bot.slash(
    name="info",
    description="Get the information about a user",
)
@app_commands.describe(user="The target user to retrieve information about")
async def _info_slash(interaction: Interaction, user: discord.User):
    embed = info.user_info(user)
    await interaction.response.send_message(embed=embed)
