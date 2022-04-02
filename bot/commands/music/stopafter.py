from discord.ext import commands

from _types import Context
from core import bot


@bot.command(
    name="stopafter",
    description="Tell the bot to disconnect after playing the current song.",
)
@commands.guild_only()
@commands.cooldown(1, 2, commands.BucketType.user)
async def _stopafter_cmd(ctx: Context):
    player = ctx.voice_client

    if not player:
        return await ctx.send("No currently connected player.")

    if await player.switch_stopafter():
        await ctx.send("Enabled `stopafter`. This will be the last song to be played.")
    else:
        await ctx.send("Disabled `stopafter`. Other songs will be played normally after this one ends.")
