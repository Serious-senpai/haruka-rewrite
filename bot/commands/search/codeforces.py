from discord.ext import commands

from _types import Context
from core import bot
from lib import codeforces, emoji_ui


@bot.command(
    name="codeforces",
    aliases=["cf"],
    description="Search for a CodeForces user(s)",
    usage="codeforces <handle(s)>",
)
@commands.cooldown(1, 2, commands.BucketType.user)
async def _codeforces_cmd(ctx: Context, *handles: str):
    try:
        users = await codeforces.User.get(handles, session=bot.session)
    except codeforces.CodeforcesException as exc:
        return await ctx.send(exc.comment)

    embeds = []
    for user in users:
        embed = user.create_embed()
        embed.set_author("CodeForces user", icon_url=bot.user.avatar.url)
        embeds.append(embed)

    if len(embeds) > 1:
        display = emoji_ui.NavigatorPagination(bot, embeds)
        await display.send(ctx.channel)
    else:
        await ctx.send(embed=embeds[0])
