import random
from typing import Literal

from discord import app_commands
from youtube_dl import utils

from _types import Interaction
from core import bot


@bot.slash(
    name="random",
    description="Random generator",
)
@app_commands.describe(category="The category to get random data")
async def _random_slash(interaction: Interaction, category: Literal["user-agent", "number"]):
    if category == "user-agent":
        await interaction.response.send_message("```\n" + utils.random_user_agent() + "\n```")
    else:
        await interaction.response.send_message(random.random())
