import slash
from _types import Interaction
from audio import MusicClient
from core import bot


json = {
    "name": "skip",
    "type": 1,
    "description": "Skip the playing song",
}


@bot.slash(json)
@slash.guild_only()
async def _skip_slash(interaction: Interaction):
    await interaction.response.defer()
    player = interaction.guild.voice_client

    if player:
        # Get current state
        shuffle = player._shuffle
        target = player.target
        channel = player.channel

        # Acknowledge the request
        await interaction.followup.send("Skipped.")

        await player.disconnect(force=True)
        voice_client = await channel.connect(
            timeout=30.0,
            cls=MusicClient,
        )
        voice_client._shuffle = shuffle

        bot.loop.create_task(voice_client.play(target=target))

    else:
        await interaction.followup.send("No currently connected player.")
