from typing import Optional

import asyncpg
import discord
from discord.ext import commands
from discord.utils import escape_markdown as escape

from core import bot


@bot.command(
    name="blacklist",
    description="Add or remove a user from blacklist.",
    usage="blacklist <user>",
)
@commands.is_owner()
async def _blacklist_cmd(ctx: commands.Context, user: discord.User, *, reason: str = "*No reason given*"):
    if user.id == ctx.author.id:
        return await ctx.send(f"Please don't blacklist yourself, <@!{ctx.author.id}>?")

    row: Optional[asyncpg.Record] = await bot.conn.fetchrow(f"SELECT * FROM blacklist WHERE id = '{user.id}';")
    if row is not None:
        await bot.conn.execute(f"DELETE FROM blacklist WHERE id = '{user.id}';")
        await ctx.send(f"Removed **{escape(str(user))}** from blacklist: {reason}", reference=ctx.message.reference)
    else:
        await bot.conn.execute(f"INSERT INTO blacklist VALUES ('{user.id}');")
        await ctx.send(f"Added **{escape(str(user))}** to blacklist: {reason}", reference=ctx.message.reference)
