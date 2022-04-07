from _types import Interaction
from core import bot
from lib import resources


@bot.slash(
    name="fact",
    description="Send you a random fact",
)
async def _fact_slash(interaction: Interaction):
    await interaction.response.send_message(resources.get_fact())
