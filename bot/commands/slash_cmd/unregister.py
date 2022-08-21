from discord import app_commands

from _types import Interaction
from core import bot
from web.routes import audio


@bot.slash(
    name="unregister",
    description="Unregister the current voice client from the web, see /register",
    official_client=False,
)
@app_commands.guild_only()
async def _unregister_slash(interaction: Interaction):
    try:
        audio.voice_manager.pop(interaction.guild.id)
    except KeyError:
        await interaction.response.send_message("The voice client in this server hasn't been registered yet")
    else:
        await interaction.response.send_message("Unregistered voice client")
