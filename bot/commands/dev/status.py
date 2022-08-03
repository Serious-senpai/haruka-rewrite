import discord
from discord.ext import commands

from _types import Context
from core import bot


@bot.command(
    name="status",
    aliases=["log"],
    description="Display the bot's `ConnectionState`",
)
@commands.is_owner()
async def _status_cmd(ctx: Context):
    await ctx.send(embed=bot.display_status, file=discord.File("./bot/web/assets/log.txt"))
    if bot.side_client:
        await bot.side_client.report(f"Sending report due to request from message ID {ctx.message.id} in channel {ctx.channel.id}")
