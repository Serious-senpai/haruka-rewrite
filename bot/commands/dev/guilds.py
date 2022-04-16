from collections import OrderedDict

import discord
from discord.ext import commands
from discord.utils import escape_markdown, utcnow

from _types import Context
from core import bot
from lib import emoji_ui, utils


GUILDS_PER_PAGE = 5


@bot.command(
    name="guilds",
    description="View guilds' information",
)
@commands.is_owner()
async def _guilds_cmd(ctx: Context):
    rows = await bot.conn.fetch("SELECT * FROM inactivity ORDER BY time;")
    if not rows:
        # This code is never reachable though
        return await ctx.send("Currently in no guilds")

    mapping = OrderedDict()
    for row in rows:
        guild = bot.get_guild(int(row["id"]))
        if guild is None:
            continue

        mapping[guild.name] = row["time"]

    pages = 1 + len(mapping) // GUILDS_PER_PAGE
    now = utcnow()
    embeds = []

    counter = 0
    for page in range(pages):
        embed = discord.Embed()
        embed.set_author(
            name="This is the guilds' information",
            icon_url=bot.user.avatar.url,
        )
        embed.set_footer(text=f"Page {page + 1}/{pages}")

        for _ in range(GUILDS_PER_PAGE):
            try:
                guild_name, last_active = mapping.popitem()
            except KeyError:
                break

            last_active = now - last_active

            counter += 1
            embed.add_field(
                name=f"#{counter} {escape_markdown(guild_name)}",
                value=f"**Last active** {utils.format(last_active.total_seconds())} ago",
                inline=False,
            )

        embeds.append(embed)

    display = emoji_ui.NavigatorPagination(bot, embeds)
    await display.send(ctx.channel)
