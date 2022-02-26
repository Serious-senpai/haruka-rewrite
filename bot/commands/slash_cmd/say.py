import slash
from _types import Interaction
from core import bot


json = {
    "name": "say",
    "type": 1,
    "description": "Say something, can be used to send animated emojis.",
    "options": [{
        "name": "content",
        "description": "The string to repeat",
        "type": 3,
        "required": True,
    }]
}


@bot.slash(json)
async def _say_slash(interaction: Interaction):
    args = slash.parse(interaction)
    await interaction.response.send_message(args["content"])
