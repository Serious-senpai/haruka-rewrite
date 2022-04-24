from discord.ext import commands

from _types import Context
from core import bot


@bot.command(
    name="sync",
    description="Sync global slash commands",
)
@commands.is_owner()
async def _sync_cmd(ctx: Context):
    commands = await bot.tree.sync()
    await ctx.send(f"Synced {len(commands)} slash commands for {bot.user}")
    commands = await bot.side_client.tree.sync()
    await ctx.send(f"Synced {len(commands)} slash commands for {bot.side_client.user}")
