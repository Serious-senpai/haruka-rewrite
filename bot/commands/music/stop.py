from discord.ext import commands

from core import bot


@bot.command(
    name="stop",
    description="Stop the playing audio and disconnect from the voice channel"
)
@commands.guild_only()
@commands.cooldown(1, 2, commands.BucketType.user)
async def _stop_cmd(ctx: commands.Context):
    player = ctx.voice_client

    if player and player.is_connected():
        await player.disconnect(force=True)
        await ctx.send("Stopped player.")
    else:
        await ctx.send("No currently connected player.")
