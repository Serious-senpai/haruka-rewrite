from typing import List

import asyncpg
import discord
from discord.ext import commands
from discord.utils import escape_markdown as escape

from core import bot


@bot.command(
    name="blacklist",
    description="Add or remove a user from blacklist.",
    usage="blacklist <user | None: view blacklist>",
)
@commands.is_owner()
async def _blacklist_cmd(ctx: commands.Context, user: discord.User = None):
    row: asyncpg.Record = await bot.conn.fetchrow("SELECT * FROM misc WHERE title = 'blacklist';")
    blacklist_ids: List[str] = row["id"]

    if not user:
        return await ctx.send(f"Currently having {len(blacklist_ids)} user(s) in blacklist.")

    if user.id == ctx.author.id:
        return await ctx.send(f"Please don't blacklist yourself, <@!{ctx.author.id}>?")

    if str(user.id) in blacklist_ids:
        await bot.conn.execute(f"""
            UPDATE misc
            SET id = array_remove(id, '{user.id}')
            WHERE title = 'blacklist';
        """)
        await ctx.send(f"Removed **{escape(str(user))}** from blacklist.")
    else:
        await bot.conn.execute(f"""
            UPDATE misc
            SET id = array_append(id, '{user.id}')
            WHERE title = 'blacklist';
        """)
        await ctx.send(f"Added **{escape(str(user))}** to blacklist.")
