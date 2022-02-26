import discord
from discord.ext import commands

from _types import Context
from core import bot


@bot.command(
    name="status",
    aliases=["state", "log"],
    description="Display the bot's `ConnectionState`",
)
@commands.is_owner()
async def _status_cmd(ctx: Context):
    await ctx.send(embed=bot.display_status, file=discord.File("./log.txt"))
