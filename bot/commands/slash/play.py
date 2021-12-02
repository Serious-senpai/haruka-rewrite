import traceback
from typing import Any, Dict, List

import discord

from audio import MusicClient
from core import bot


json: Dict[str, Any] = {
    "name": "play",
    "type": 1,
    "description": "Start playing the queue of the voice channel you are connected to.",
}


@bot.slash(json)
async def _play_slash(interaction: discord.Interaction):
    await interaction.response.defer()
    if not isinstance(interaction.user, discord.Member):
        await interaction.followup.send("Cannot start playing music right now.")

    elif not interaction.user.voice:
        await interaction.followup.send("Please join a voice channel first.")

    else:
        vchannel: discord.abc.Connectable = interaction.user.voice.channel

        queue: List[str] = await MusicClient.queue(vchannel.id)
        if len(queue) == 0:
            return await interaction.followup.send("Please add a song to the queue with `add`")

        if interaction.guild.voice_client:
            return await interaction.followup.send("Currently connected to another voice channel in the server. Please use `stop` first.")

        try:
            voice_client: MusicClient = await vchannel.connect(
                timeout = 30.0,
                cls = MusicClient,
            )
        except:
            bot.log(f"Error connecting to voice channel {vchannel.guild}/{vchannel}")
            bot.log(traceback.format_exc())
            return await interaction.followup.send("Cannot connect to voice channel.")

        await interaction.followup.send(f"Connected to <#{vchannel.id}>")
        bot.loop.create_task(voice_client.play(target = interaction.channel))
