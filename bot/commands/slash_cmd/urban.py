from discord import app_commands

from _types import Interaction
from core import bot
from lib import urban


@bot.slash(
    name="urban",
    description="Search Urban Dictionary for a term",
)
@app_commands.describe(word="The word to look up")
async def _urban_slash(interaction: Interaction, word: str):
    await interaction.response.defer()

    result = await urban.UrbanSearch.search(word, session=bot.session)
    if result:
        embed = result.create_embed()
        embed.set_author(
            name=f"This is the definition of {word}",
            icon_url=bot.user.avatar.url,
        )
        await interaction.followup.send(embed=embed)
    else:
        await interaction.followup.send(content="No matching result was found.")
