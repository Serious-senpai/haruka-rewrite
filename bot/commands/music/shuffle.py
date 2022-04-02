from discord.ext import commands

from _types import Context
from core import bot


@bot.command(
    name="shuffle",
    description="Enable/Disable music playing shuffle",
)
@commands.guild_only()
@commands.cooldown(1, 2, commands.BucketType.user)
async def _shuffle_cmd(ctx: Context):
    player = ctx.voice_client

    if player:
        if await player.switch_shuffle():
            await ctx.send("Shuffle has been turned on. Songs will be played randomly.")
        else:
            await ctx.send("Shuffle has been turned off. Songs will be played with the queue order.")
    else:
        await ctx.send("No audio client detected in this server.")
