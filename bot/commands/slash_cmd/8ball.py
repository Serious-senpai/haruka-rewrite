from discord import app_commands

import leech
from _types import Interaction
from core import bot


@bot.slash(
    name="8ball",
    description="Ask the 8ball a question",
)
@app_commands.describe(question="Concentrate on your question and press `Enter`")
async def _8ball_slash(interaction: Interaction, question: str):
    await interaction.response.send_message(leech.get_8ball())
