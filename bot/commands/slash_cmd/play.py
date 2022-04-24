import traceback

import discord

from _types import Interaction
from core import bot
from lib.audio import MusicClient


@bot.slash(
    name="play",
    description="Start playing the queue of the voice channel you are connected to.",
    verified_client=False,
)
@bot.audio.in_voice(slash_command=True)
async def _play_slash(interaction: Interaction):
    await interaction.response.defer()
    vchannel = interaction.user.voice.channel

    queue = await bot.audio.queue(vchannel.id)
    if len(queue) == 0:
        return await interaction.followup.send("Please add a song to the queue with `add` or `playlist`")

    if interaction.guild.voice_client:
        return await interaction.followup.send("Currently connected to another voice channel in the server. Please use `stop` first.")

    try:
        voice_client = await vchannel.connect(timeout=30.0, cls=MusicClient)
    except BaseException:
        bot.log(f"Error connecting to voice channel {vchannel.guild}/{vchannel}")
        bot.log(traceback.format_exc())
        return await interaction.followup.send("Cannot connect to voice channel.")

    await interaction.followup.send(f"Connected to <#{vchannel.id}>")
    bot.loop.create_task(voice_client.play(target=interaction.channel))
