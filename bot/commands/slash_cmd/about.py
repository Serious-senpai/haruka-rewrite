from _types import Interaction
from core import bot
from lib import info


@bot.slash(
    name="about",
    description="Display bot's information",
)
async def _about_slash(interaction: Interaction):
    embed = info.user_info(interaction.client.user)
    embed.add_field(
        name="Nerfed Haruka",
        value="[Invite link](https://discord.com/api/oauth2/authorize?client_id=870160931219439667&permissions=388160&scope=bot%20applications.commands)",
        inline=False
    )
    embed.add_field(
        name="Haruka's Original Form",
        value="Support text commands, music, NSFW images and much more...\n[Invite link](https://discord.com/api/oauth2/authorize?client_id=848178172536946708&permissions=1099514899718&scope=bot%20applications.commands)",
        inline=False,
    )
    await interaction.response.send_message(embed=embed)
