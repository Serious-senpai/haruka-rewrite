from discord.ext import commands

from _types import Context
from core import bot
from lib.audio import MusicClient
from lib.emoji_ui import CHECKER


@bot.command(
    name="skip",
    description="Skip the playing song."
)
@commands.guild_only()
@commands.cooldown(1, 2, commands.BucketType.user)
async def _skip_cmd(ctx: Context):
    player = ctx.voice_client

    if player:
        # Get current state
        shuffle = player.shuffle
        target = player.target
        channel = player.channel

        # Acknowledge the request
        await ctx.message.add_reaction(CHECKER[1])

        await player.disconnect(force=True)
        voice_client = await channel.connect(timeout=30.0, cls=MusicClient)
        voice_client._shuffle = shuffle

        bot.loop.create_task(voice_client.play(target=target))

    else:
        await ctx.send("No currently connected player.")
