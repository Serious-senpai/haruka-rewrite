from typing import Optional

from discord.ext import commands

from audio import MusicClient
from core import bot


@bot.command(
    name="repeat",
    description="Switch between `REPEAT ONE` and `REPEAT ALL`",
)
@commands.guild_only()
@commands.cooldown(1, 2, commands.BucketType.user)
async def _repeat_cmd(ctx: commands.Context):
    player: Optional[MusicClient] = ctx.voice_client

    if player:
        await player._operable.wait()
        player._repeat = not player._repeat

        if player._repeat:
            await ctx.send("Switched to `REPEAT ONE` mode. The current song will be play repeatedly.")
        else:
            await ctx.send("Switched to `REPEAT ALL` mode. All songs will be played as normal.")

    await ctx.send("No audio is currently being played to pause.")
