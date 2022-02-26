import leech
from _types import Interaction
from core import bot


json = {
    "name": "fact",
    "type": 1,
    "description": "Send you a random fact.",
}


@bot.slash(json)
async def _fact_slash(interaction: Interaction):
    await interaction.response.send_message(leech.get_fact())
