from discord import app_commands

from _types import Interaction
from core import bot


@bot.slash(
    name="say",
    description="Say something, can be used to send animated emojis",
)
@app_commands.describe(content="The string to repeat")
async def _say_slash(interaction: Interaction, content: str):
    await interaction.response.send_message(content)
