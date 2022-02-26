from discord.ext import commands

from _types import Context
from core import bot


@bot.command(
    name="repeat",
    description="Switch between `REPEAT ONE` and `REPEAT ALL`",
)
@commands.guild_only()
@commands.cooldown(1, 2, commands.BucketType.user)
async def _repeat_cmd(ctx: Context):
    player = ctx.voice_client

    if player:
        await player.operable.wait()
        player._repeat = not player._repeat

        if player._repeat:
            await ctx.send("Switched to `REPEAT ONE` mode. The current song will be played repeatedly.")
        else:
            await ctx.send("Switched to `REPEAT ALL` mode. All songs will be played as normal.")

    else:
        await ctx.send("No audio is currently being played.")
