import random

from youtube_dl import utils

import slash
from _types import Interaction
from core import bot


json = {
    "name": "random",
    "type": 1,
    "description": "Random generator",
    "options": [
        {
            "name": "user-agent",
            "description": "Generate a random User-Agent header",
            "type": 1,
        },
        {
            "name": "number",
            "description": "Generate a random number in the [0, 1) range",
            "type": 1,
        }
    ]
}


@bot.slash(json)
async def _random_slash(interaction: Interaction):
    args = slash.parse(interaction)
    if args.get("user-agent"):
        await interaction.response.send_message("```\n" + utils.random_user_agent() + "\n```")
    elif args.get("number"):
        await interaction.response.send_message(random.random())
