import random

from discord import app_commands

from _types import Interaction
from core import bot


@bot.slash(
    name="roll",
    description="Generate a random number between 2 integers",
)
@app_commands.describe(
    first_integer="The first limit integer",
    second_integer="The second limit integer",
)
async def _roll_slash(interaction: Interaction, first_integer: int, second_integer: int):
    i = first_integer
    j = second_integer
    ans = random.randint(i, j) if i < j else random.randint(j, i)

    await interaction.response.send_message(f"<@!{interaction.user.id}> got **{ans}**")
