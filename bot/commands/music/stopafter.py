from discord.ext import commands

from core import bot


@bot.command(
    name="stopafter",
    description="Tell the bot to disconnect after playing the current song.",
)
@commands.guild_only()
@commands.cooldown(1, 2, commands.BucketType.user)
async def _stopafter_cmd(ctx: commands.Context):
    player = ctx.voice_client

    if not player:
        return await ctx.send("No currently connected player.")

    player._stopafter = not player._stopafter
    if player._stopafter:
        await ctx.send("Enabled `stopafter`. This will be the last song to be played.")
    else:
        await ctx.send("Disabled `stopafter`. Other songs will be played normally after this one ends.")
