import discord

import _pixiv
import slash
from core import bot


json = {
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
    args = slash.parse(interaction)
    query = args["string"]

    try:
        parsed = await _pixiv.parse(query, session=bot.session)
    except _pixiv.NSFWArtworkDetected as exc:
        parsed = exc.artwork
        if isinstance(interaction.channel, discord.TextChannel) and not interaction.channel.is_nsfw():
            return await interaction.followup.send("🔞 This artwork is NSFW and can only be shown in a NSFW channel!")

    if isinstance(parsed, list):
        try:
            parsed = parsed[0]
        except IndexError:
            return await interaction.followup.send("No matching result was found.")

    await interaction.followup.send(embed=await parsed.create_embed(session=bot.session))
