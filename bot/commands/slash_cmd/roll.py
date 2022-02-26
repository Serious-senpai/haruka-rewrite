import random

import slash
from _types import Interaction
from core import bot


json = {
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
async def _roll_slash(interaction: Interaction):
    args = slash.parse(interaction)
    i = args["first-integer"]
    j = args["second-integer"]

    if i < j:
        ans = random.randint(i, j)
    else:
        ans = random.randint(j, i)

    await interaction.response.send_message(f"<@!{interaction.user.id}> got **{ans}**")
