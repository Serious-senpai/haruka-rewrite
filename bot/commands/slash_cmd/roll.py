import random
from typing import Any, Dict

import discord

import slash
from core import bot


json: Dict[str, Any] = {
    "name": "roll",
    "type": 1,
    "description": "Generate a random number between 2 integers.",
    "options": [
        {
            "name": "first-integer",
            "description": "The first limit integer",
            "type": 4,
            "required": True,
        },
        {
            "name": "second-integer",
            "description": "The second limit integer",
            "type": 4,
            "required": True,
        },
    ]
}


@bot.slash(json)
async def _roll_slash(interaction: discord.Interaction):
    await interaction.response.defer()
    args: Dict[str, int] = slash.parse(interaction)
    i: int = args["first-integer"]
    j: int = args["second-integer"]

    if i < j:
        ans: int = random.randint(i, j)
    else:
        ans: int = random.randint(j, i)

    await interaction.followup.send(f"<@!{interaction.user.id}> got **{ans}**")
