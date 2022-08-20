from discord.ext import commands

from _types import Context
from core import bot
from lib.emoji_ui import CHECKER


@bot.command(
    name="skip",
    description="Skip the playing song."
)
@commands.guild_only()
@commands.cooldown(1, 2, commands.BucketType.user)
async def _skip_cmd(ctx: Context):
    player = ctx.voice_client

    if player:
        await ctx.message.add_reaction(CHECKER[1])
        await player.skip()

    else:
        await ctx.send("No currently connected player.")
