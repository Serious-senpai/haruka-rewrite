from typing import Optional

import discord
from discord.ext import commands
from discord.utils import escape_markdown as escape

from _types import Context
from core import bot
from lib import emoji_ui


@bot.command(
    name="blacklist",
    description="Add or remove a user from blacklist.",
    usage="blacklist <user>",
)
@commands.is_owner()
async def _blacklist_cmd(ctx: Context, user: Optional[discord.User], *, reason: str = "*No reason given*"):
    if user is not None:
        if user.id == ctx.author.id:
            return await ctx.send(f"Please don't blacklist yourself, <@!{ctx.author.id}>?")

        row = await bot.conn.fetchrow(f"SELECT * FROM blacklist WHERE id = '{user.id}';")
        if row is not None:
            await bot.conn.execute(f"DELETE FROM blacklist WHERE id = '{user.id}';")
            await ctx.send(f"Removed **{escape(str(user))}** from blacklist: {reason}", reference=ctx.message.reference)
        else:
            await bot.conn.execute(f"INSERT INTO blacklist VALUES ('{user.id}');")
            await ctx.send(f"Added **{escape(str(user))}** to blacklist: {reason}", reference=ctx.message.reference)

    else:
        rows = await bot.conn.fetch("SELECT * FROM blacklist;")
        if not rows:
            return await ctx.send("The blacklist is currently empty!")

        embeds = []
        for index, row in enumerate(rows):
            if index % 10 == 0:
                embed = discord.Embed()
                embed.set_author(name="These are blacklisted users", icon_url=bot.user.avatar.url)
                embed.set_footer(text=f"{len(rows)} user(s) in total")
                embeds.append(embed)

            user = await bot.fetch_user(row["id"])  # Union[str, int]
            embed = embeds[-1]
            embed.description += f"\n**#{index + 1}** {user}"

        display = emoji_ui.NavigatorPagination(bot, embeds)
        await display.send(ctx.channel)
