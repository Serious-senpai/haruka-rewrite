from typing import Optional

from discord.ext import commands

from audio import MusicClient
from core import bot


@bot.command(
    name="stopafter",
    description="Tell the bot to disconnect after playing the current song.",
)
@commands.guild_only()
@commands.cooldown(1, 5, commands.BucketType.user)
async def _stopafter_cmd(ctx: commands.Context):
    player: Optional[MusicClient] = ctx.voice_client

    if not player:
        return await ctx.send("No currently connected player.")

    player._stopafter = not player._stopafter
    if player._stopafter:
        await ctx.send("Enabled `stopafter`. This will be the last song to be played.")
    else:
        await ctx.send("Disabled `stopafter`. Other songs will be played normally after this one ends.")
