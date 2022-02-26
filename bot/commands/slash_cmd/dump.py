import slash
from _types import Interaction
from core import bot


bot._dump_bin = {}
json = {
    "name": "dump",
    "type": 1,
    "description": "This command does nothing.",
    "options": [
        {
            "name": "string",
            "description": "A string",
            "type": 3,
            "required": False,
        },
        {
            "name": "integer",
            "description": "An integer",
            "type": 4,
            "required": False,
        },
        {
            "name": "boolean",
            "description": "A boolean",
            "type": 5,
            "required": False,
        },
        {
            "name": "user",
            "description": "A user",
            "type": 6,
            "required": False,
        },
        {
            "name": "channel",
            "description": "A channel",
            "type": 7,
            "required": False,
        },
        {
            "name": "role",
            "description": "A role",
            "type": 8,
            "required": False,
        },
    ]
}


@bot.slash(json)
async def _test_slash(interaction: Interaction):
    await interaction.response.defer()
    args = slash.parse(interaction)
    content = "```"

    for key, arg in args.items():
        content += f"\n{key} ({arg.__class__.__name__}): {arg}"

    content += "\n```"
    bot._dump_bin[interaction.id] = interaction
    await interaction.followup.send(content)
