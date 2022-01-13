from discord.ext import commands

from core import bot


@bot.command(
    name="pause",
    description="Pause the playing audio",
)
@commands.guild_only()
@commands.cooldown(1, 2, commands.BucketType.user)
async def _pause_cmd(ctx: commands.Context):
    player = ctx.voice_client

    if player:
        await player.operable.wait()
        if player.is_playing():
            player.pause()
            return await ctx.send("Paused audio.")

    await ctx.send("No audio is currently being played to pause.")
