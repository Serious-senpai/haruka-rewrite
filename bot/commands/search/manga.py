import discord
from discord.ext import commands
from discord.utils import escape_markdown as escape

import mal
import emoji_ui
from _types import Context
from core import bot
from emoji_ui import CHOICES


@bot.command(
    name="manga",
    description="Search for a manga in the MyAnimeList database",
    usage="manga <query>"
)
@commands.cooldown(1, 2, commands.BucketType.user)
async def _manga_cmd(ctx: Context, *, query):
    if len(query) < 3:
        await ctx.send(f"Search query must have at least 3 characters")
        return

    rslt = await mal.MALSearchResult.search(query, criteria="manga")

    if not rslt:
        return await ctx.send("No matching result was found.")

    desc = "\n".join(f"{CHOICES[i[0]]} {i[1].title}" for i in enumerate(rslt))
    embed = discord.Embed(
        title=f"Search results for {query}",
        description=escape(desc),
    )
    message = await ctx.send(embed=embed)

    display = emoji_ui.SelectMenu(message, len(rslt))
    choice = await display.listen(ctx.author.id)

    if choice is not None:
        manga = await mal.Manga.get(rslt[choice].id)
        if manga:
            embed = manga.create_embed()
            embed.set_author(
                name=f"{ctx.author.name}'s request",
                icon_url=ctx.author.avatar.url if ctx.author.avatar else None,
            )
            await ctx.send(embed=embed)
        else:
            return await ctx.send("An unexpected error has occurred.")
