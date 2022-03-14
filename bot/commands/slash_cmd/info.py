import discord
from discord import app_commands

import _info
from _types import Interaction
from core import bot


@bot.slash(
    name="info",
    description="Get the information about a user",
)
@app_commands.describe(user="The target user to retrieve information about")
async def _info_slash(interaction: Interaction, user: discord.User):
    embed = _info.user_info(user)
    await interaction.response.send_message(embed=embed)
