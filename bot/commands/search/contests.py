from discord.ext import commands

from _types import Context
from core import bot
from lib import codeforces, emoji_ui


@bot.command(
    name="contests",
    description="Display a list of 30 CodeForces contests",
    usage="contests <handle(s)>",
)
@commands.cooldown(1, 8, commands.BucketType.user)
async def _contests_cmd(ctx: Context):
    try:
        contests = await codeforces.Contest.list(session=bot.session, limit=30)
    except codeforces.CodeforcesException as exc:
        return await ctx.send(exc.comment)

    embeds = [contest.create_embed() for contest in contests]
    breakpoint = None
    for index, contest in enumerate(contests):
        if contest.relative_time is not None:
            if contest.relative_time.total_seconds() < 0:
                break

            breakpoint = index

    if breakpoint is not None:
        display = emoji_ui.StackedNavigatorPagination(bot, embeds, [0, breakpoint])
    else:
        display = emoji_ui.NavigatorPagination(bot, embeds)

    await display.send(ctx.channel)
