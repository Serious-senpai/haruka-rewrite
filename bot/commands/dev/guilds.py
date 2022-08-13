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
    guilds = list(bot.guilds)
    pages = 1 + len(guilds) // GUILDS_PER_PAGE
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
                guild = guilds.pop()
            except IndexError:
                break

            counter += 1
            embed.add_field(
                name=f"#{counter} {escape_markdown(guild.name)}",
                value=f"**Joined** {utils.format((now - guild.me.joined_at).total_seconds())} ago",
                inline=False,
            )

        embeds.append(embed)

    display = emoji_ui.NavigatorPagination(bot, embeds)
    await display.send(ctx.channel)
