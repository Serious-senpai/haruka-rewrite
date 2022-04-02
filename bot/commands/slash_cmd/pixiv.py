import discord
from discord import app_commands

from _types import Interaction
from core import bot
from lib import pixiv


@bot.slash(
    name="pixiv",
    description="Search for an artwork from Pixiv",
)
@app_commands.describe(query="The searching query, a URL or an ID")
async def _pixiv_slash(interaction: Interaction, query: str):
    await interaction.response.defer()
    try:
        parsed = await pixiv.parse(query, session=bot.session)
    except pixiv.NSFWArtworkDetected as exc:
        parsed = exc.artwork
        if isinstance(interaction.channel, discord.TextChannel) and not interaction.channel.is_nsfw():
            return await interaction.followup.send("🔞 This artwork is NSFW and can only be shown in a NSFW channel!")

    if isinstance(parsed, list):
        try:
            parsed = parsed[0]
        except IndexError:
            return await interaction.followup.send("No matching result was found.")

    await interaction.followup.send(embed=await parsed.create_embed(session=bot.session))
