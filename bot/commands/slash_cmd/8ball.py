from discord import app_commands

from _types import Interaction
from core import bot
from lib import resources


@bot.slash(
    name="8ball",
    description="Ask the 8ball a question",
)
@app_commands.describe(question="Concentrate on your question and press `Enter`")
async def _8ball_slash(interaction: Interaction, question: str):
    await interaction.response.send_message(resources.get_8ball())
