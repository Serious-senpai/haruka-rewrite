import discord
from discord.ext import commands
from discord.utils import escape_markdown as escape

from _types import Context
from core import bot
from lib import emoji_ui, mal
from lib.emoji_ui import CHOICES


@bot.command(
    name="anime",
    description="Search for an anime in the MyAnimeList database",
    usage="anime <query>"
)
@commands.cooldown(1, 2, commands.BucketType.user)
async def _anime_cmd(ctx: Context, *, query):
    if len(query) < 3:
        await ctx.send(f"Search query must have at least 3 characters")
        return

    results = await mal.MALSearchResult.search(query, criteria="anime", session=bot.session)

    if not results:
        return await ctx.send("No matching result was found.")

    desc = "\n".join(f"{CHOICES[i[0]]} {i[1].title}" for i in enumerate(results))
    embed = discord.Embed(
        title=f"Search results for {query}",
        description=escape(desc),
    )
    message = await ctx.send(embed=embed)

    display = emoji_ui.SelectMenu(bot, message, len(results))
    choice = await display.listen(ctx.author.id)

    if choice is not None:
        anime = await mal.Anime.get(results[choice].id, session=bot.session)
        if anime:

            if not anime.is_safe() and not getattr(ctx.channel, "nsfw", False):
                return await ctx.send("🔞 This anime contains NSFW content and cannot be displayed in this channel!")

            embed = anime.create_embed()
            embed.set_author(
                name=f"{ctx.author.name}'s request",
                icon_url=ctx.author.avatar.url if ctx.author.avatar else None,
            )
            await ctx.send(embed=embed)
        else:
            return await ctx.send("An unexpected error has occurred.")
