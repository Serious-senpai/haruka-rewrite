import re
from typing import Any, Dict, List, Optional

import discord

import _pixiv
import slash_utils
from core import bot


json: Dict[str, Any] = {
    "name": "pixiv",
    "type": 1,
    "description": "Search for an artwork from Pixiv",
    "options": [{
        "name": "string",
        "description": "The searching query, a URL or an ID",
        "type": 3,
        "required": True,
    }]
}


@bot.slash(json)
async def _pixiv_slash(interaction: discord.Interaction):
    await interaction.response.defer()
    args: Dict[str, str] = slash_utils.parse(interaction)
    query: str = args["string"]

    id: int
    artwork: _pixiv.PixivArtwork

    id_match: Optional[re.Match] = _pixiv.ID_PATTERN.fullmatch(query)
    if id_match:
        id = int(id_match.group())
        artwork = await _pixiv.PixivArtwork.from_id(id)

    elif re.match(r"https://", query):
        match = _pixiv.ID_PATTERN.search(query)
        if not match:
            return await interaction.followup.send("Invalid URL.")
        else:
            id = int(match.group())
            artwork = await _pixiv.PixivArtwork.from_id(id)

    else:
        # Get the first Pixiv result from query
        if len(query) < 2:
            return await interaction.followup.send("Search query must have at least 2 characters")

        rslt: List[_pixiv.PixivArtwork] = await _pixiv.PixivArtwork.search(query)
        if not rslt:
            return await interaction.followup.send("No matching result was found.")

        artwork = rslt[0]

    if isinstance(interaction.channel, discord.TextChannel):
        if artwork.nsfw and not interaction.channel.is_nsfw():
            return await interaction.followup.send("🔞 This artwork is NSFW and can only be shown in a NSFW channel!")

    embed: discord.Embed = await artwork.create_embed()
    embed.set_author(
        name="Pixiv searching request",
        icon_url=bot.user.avatar.url,
    )
    return await interaction.followup.send(embed=embed)
