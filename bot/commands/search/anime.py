import discord
from discord.ext import commands
from discord.utils import escape_markdown as escape

import mal
import emoji_ui
from core import bot
from emoji_ui import CHOICES


@bot.command(
    name="anime",
    description="Search for an anime in the MyAnimeList database",
    usage="anime <query>"
)
@commands.cooldown(1, 2, commands.BucketType.user)
async def _anime_cmd(ctx: commands.Context, *, query):
    if len(query) < 3:
        await ctx.send(f"Search query must have at least 3 characters")
        return

    rslt = await mal.MALSearchResult.search(query, criteria="anime")

    if not rslt:
        return await ctx.send("No matching result was found.")

    desc = "\n".join(f"{CHOICES[i[0]]} {i[1].title}" for i in enumerate(rslt))
    em = discord.Embed(
        title=f"Search results for {query}",
        description=escape(desc),
    )
    message = await ctx.send(embed=em)

    display = emoji_ui.SelectMenu(message, len(rslt))
    choice = await display.listen(ctx.author.id)

    if choice is not None:
        anime = await mal.Anime.get(rslt[choice].id)
        if anime:
            em = anime.create_embed()
            em.set_author(
                name=f"{ctx.author.name}'s request",
                icon_url=ctx.author.avatar.url if ctx.author.avatar else discord.Embed.Empty,
            )
            await ctx.send(embed=em)
        else:
            return await ctx.send("An unexpected error has occurred.")
