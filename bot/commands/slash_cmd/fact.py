from _types import Interaction
from core import bot
from lib import leech


@bot.slash(
    name="fact",
    description="Send you a random fact",
)
async def _fact_slash(interaction: Interaction):
    await interaction.response.send_message(leech.get_fact())
