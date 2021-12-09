from typing import Any, Dict, Optional

import discord

import slash
from audio import MusicClient
from core import bot


json: Dict[str, Any] = {
    "name": "skip",
    "type": 1,
    "description": "Skip the playing song",
}


@bot.slash(json)
@slash.guild_only()
async def _skip_slash(interaction: discord.Interaction):
    await interaction.response.defer()
    player: Optional[MusicClient] = interaction.guild.voice_client

    if player:
        # Get current state
        shuffle: bool = player._shuffle
        target: discord.abc.Messageable = player.target
        channel: discord.abc.Connectable = player.channel

        # Acknowledge the request
        await interaction.followup.send("Skipped.")

        await player.disconnect(force=True)
        voice_client: MusicClient = await channel.connect(
            timeout=30.0,
            cls=MusicClient,
        )
        voice_client._shuffle = shuffle

        bot.loop.create_task(voice_client.play(target=target))

    else:
        await interaction.followup.send("No currently connected player.")
