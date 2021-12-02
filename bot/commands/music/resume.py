from typing import Optional

from discord.ext import commands

from audio import MusicClient
from core import bot


@bot.command(
    name = "resume",
    description = "Resume the paused audio"
)
@commands.guild_only()
@commands.cooldown(1, 5, commands.BucketType.user)
async def _resume_cmd(ctx: commands.Context):
    player: Optional[MusicClient] = ctx.voice_client

    if player:
        await player._operable.wait()
        if player.is_paused():
            player.resume()
            return await ctx.send("Resumed audio.")

    await ctx.send("No audio is currently being paused to resume.")
