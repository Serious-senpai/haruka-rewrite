from discord.ext import commands

from _types import Context
from core import bot


@bot.command(
    name="resume",
    description="Resume the paused audio"
)
@commands.guild_only()
@commands.cooldown(1, 2, commands.BucketType.user)
async def _resume_cmd(ctx: Context):
    player = ctx.voice_client

    if player:
        await player.operable.wait()
        if player.is_paused():
            player.resume()
            return await ctx.send("Resumed audio.")

    await ctx.send("No audio is currently being paused to resume.")
