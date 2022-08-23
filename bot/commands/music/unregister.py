from discord.ext import commands

from _types import Context
from core import bot
from web.routes import audio


@bot.command(
    name="unregister",
    description="Unregister the current voice client from the web.\nSee also: `{prefix}register`",
)
@commands.guild_only()
@commands.cooldown(1, 2, commands.BucketType.user)
async def _unregister_cmd(ctx: Context):
    try:
        audio.voice_manager.pop(ctx.guild.id)
    except KeyError:
        await ctx.send("The voice client in this server hasn't been registered yet")
    else:
        await ctx.send("Unregistered voice client")
