from discord import app_commands

from _types import Interaction
from core import bot
from lib import codeforces


@bot.slash(
    name="codeforces",
    description="Display information about a CodeForces user",
)
@app_commands.describe(handle="A CodeForces username")
async def _codeforces_slash(interaction: Interaction, handle: str):
    await interaction.response.defer()
    try:
        user = await codeforces.User.get(handle, session=bot.session)
    except codeforces.CodeforcesException as exc:
        return await interaction.followup.send(exc.comment)

    embed = user[0].create_embed()
    embed.set_author(name="CodeForces user", icon_url=interaction.client.user.avatar.url)
    await interaction.followup.send(embed=embed)
