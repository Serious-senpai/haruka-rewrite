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
    description="View the guild auto-leaving scheduler",
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
            await bot.conn.execute("DELETE FROM inactivity WHERE id = $1;", row["id"])
            continue

        mapping[guild.name] = row["time"]

    pages = 1 + len(mapping) // GUILDS_PER_PAGE
    now = utcnow()
    embeds = []

    for page in range(pages):
        embed = discord.Embed()
        embed.set_author(
            name="This is the auto-leaving scheduler",
            icon_url=bot.user.avatar.url,
        )
        embed.set_footer(text=f"Page {page + 1}/{pages}")

        guild_names = []
        last_active_time = []
        for _ in range(GUILDS_PER_PAGE):
            try:
                guild_name, last_active = mapping.popitem()
            except KeyError:
                break

            last_active = now - last_active
            guild_names.append(escape_markdown(guild_name))
            last_active_time.append(f"{utils.format(last_active.seconds)} ago")

        embed.add_field(name="Guilds", value="\n".join(guild_names))
        embed.add_field(name="Last active time", value="\n".join(last_active_time))
        embeds.append(embed)

    display = emoji_ui.NavigatorPagination(bot, embeds)
    await display.send(ctx.channel)
