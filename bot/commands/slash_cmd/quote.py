from typing import Optional

from discord import app_commands

import leech
from _types import Interaction
from core import bot


@bot.slash(
    name="quote",
    description="Send a random anime quote",
)
@app_commands.describe(anime="The anime name to get the quote, leave blank to get a random one.")
async def _quote_slash(interaction: Interaction, anime: Optional[str]):
    await interaction.response.defer()
    await interaction.followup.send(embed=await leech.get_quote(anime))
