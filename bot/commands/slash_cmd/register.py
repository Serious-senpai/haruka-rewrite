from discord import app_commands

from _types import Interaction
from core import bot
from env import HOST
from web.routes import audio


@bot.slash(
    name="register",
    description="Register the current voice client to be able to control via the web browser",
    official_client=False,
)
@app_commands.guild_only()
async def _register_slash(interaction: Interaction):
    client = interaction.guild.voice_client
    if client and client.is_connected():
        key = audio.voice_manager.push(interaction.guild.id)
        url = HOST + f"/audio-control?key={key}"
        await interaction.response.send_message(f"You can now control the music player via {url}")

    else:
        await interaction.response.send_message("No currently connected player.")
