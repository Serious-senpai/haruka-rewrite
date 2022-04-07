from discord.ext import commands

from _types import Context
from core import bot
from lib.quotes import Quote


@bot.command(
    name="quote",
    description="Send you a random anime quote.",
    usage="quote <anime | default: random>",
)
@commands.cooldown(1, 2, commands.BucketType.user)
async def _quote_cmd(ctx: Context, *, anime: str = None):
    quote = await Quote.get(anime)
    await ctx.send(embed=quote.create_embed(icon_url=bot.user.avatar.url))
