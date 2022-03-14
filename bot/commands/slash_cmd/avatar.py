import discord
from discord import app_commands

from _types import Interaction
from core import bot


@bot.slash(
    name="avatar",
    description="Get the avatar from a user",
)
@app_commands.describe(user="The target user to get the avatar from")
async def _avatar_slash(interaction: Interaction, user: discord.User):
    embed = discord.Embed()
    embed.set_author(
        name=f"This is {user.name}'s avatar",
        icon_url=bot.user.avatar.url,
    )
    embed.set_image(url=user.avatar.url if user.avatar else None)
    await interaction.response.send_message(embed=embed)
