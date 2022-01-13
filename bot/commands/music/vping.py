from discord.ext import commands

import utils
from core import bot


@bot.command(
    name="vping",
    aliases=["vp"],
    description="Ping the connected voice client in this server.",
)
@commands.guild_only()
@commands.cooldown(1, 2, commands.BucketType.user)
async def _vping_cmd(ctx: commands.Context):
    player = ctx.voice_client

    if player and player.is_connected():
        await player.operable.wait()
        await ctx.send(f"🏓 Pong! Connecting to <#{player.channel.id}> at `{player.ws.gateway}` with {utils.format(player.latency)} latency")
    else:
        await ctx.send("No currently connected player.")
