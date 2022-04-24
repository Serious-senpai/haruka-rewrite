from typing import Optional

from discord import app_commands

from _types import Interaction
from core import bot
from lib.quotes import Quote


@bot.slash(
    name="quote",
    description="Send a random anime quote",
)
@app_commands.describe(anime="The anime name to get the quote, leave blank to get a random one.")
async def _quote_slash(interaction: Interaction, anime: Optional[str]):
    await interaction.response.defer()
    quote = await Quote.get(anime)
    await interaction.followup.send(embed=quote.create_embed(icon_url=interaction.client.user.avatar.url))
