from typing import Any, Dict

import discord

import slash_utils
from core import bot


json: Dict[str, Any] = {
    "name": "avatar",
    "type": 1,
    "description": "Get the avatar from a user.",
    "options": [{
        "name": "user",
        "description": "The target user to get the avatar from",
        "type": 6,
        "required": False,
    }]
}


@bot.slash(json)
async def _avatar_slash(interaction: discord.Interaction):
    args: Dict[str, discord.User] = slash_utils.parse(interaction)
    user: discord.User = args.get("user", interaction.user)

    embed: discord.Embed = discord.Embed(color = 0x2ECC71)
    embed.set_author(
        name = f"This is {user.name}'s avatar",
        icon_url = bot.user.avatar.url,
    )
    embed.set_image(url = user.avatar.url if user.avatar else discord.Embed.Empty)
    await interaction.response.send_message(embed = embed)
