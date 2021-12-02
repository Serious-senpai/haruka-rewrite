import io
import sys
import time
from typing import List, Optional

import discord
from discord.ext import commands
from discord.utils import escape_markdown as escape

import audio
import emoji_ui
from core import bot
from emoji_ui import CHOICES


@bot.command(
    name = "youtube",
    aliases = ["yt"],
    description = "Search for a YouTube video and get the mp3 file.\nMaximum file size is 8 MB regardless of the server's upload limit.",
    usage = "youtube <query>",
)
@commands.cooldown(1, 15, commands.BucketType.user)
async def _youtube_cmd(ctx: commands.Context, *, query: str):
    if len(query) < 3:
        return await ctx.send("Search query must have at least 3 characters")

    t: float = time.perf_counter()
    results: List[audio.PartialInvidiousSource] = await audio.PartialInvidiousSource.search(query)
    _t: float = time.perf_counter()

    if not results:
        return await ctx.send(f"Cannot find any videos from the query `{query}`")

    em: discord.Embed = discord.Embed(
        title = f"Search results for {query}",
        color = 0x2ECC71,
    )

    for index, track in enumerate(results[:6]):
        em.add_field(
            name = f"{CHOICES[index]} {escape(track.title)}",
            value = escape(track.channel),
            inline = False,
        )

    em.set_author(
        name = f"{ctx.author.name} searched YouTube",
        icon_url = ctx.author.avatar.url if ctx.author.avatar else discord.Embed.Empty,
    )
    em.set_footer(text = "Done searching in {:.2f} ms".format(1000 * (_t - t)))
    msg: discord.Message = await ctx.send(embed = em)

    board: emoji_ui.SelectMenu = emoji_ui.SelectMenu(msg, len(results))
    choice: Optional[int] = await board.listen(ctx.author.id)

    if choice is None:
        return

    source: audio.InvidiousSource = await audio.InvidiousSource.build(results[choice].id)
    url: str = await source.get_source()
    em: discord.Embed = source.create_embed()
    em.set_author(
        name = f"{ctx.author.name}'s request",
        icon_url = ctx.author.avatar.url if ctx.author.avatar else discord.Embed.Empty,
    )

    async with ctx.typing():
        async with bot.session.get(url) as response:
            # Sometimes the link Invidious gave us is
            # 403 Forbidden or something idk, just do
            # a check here.
            if not response.ok:
                em.set_footer(text = f"Cannot fetch the audio, HTTP code {response.status}")
                await ctx.send(embed = em)
            else:
                t: float = time.perf_counter()
                data: bytes = await audio.fetch(url)
                _t: float = time.perf_counter()

                if sys.getsizeof(data) > 8 << 20:
                    em.set_footer(text = "Output exceeded file size limit.")
                    await ctx.send(embed = em)
                else:
                    em.set_footer(
                        text = "Fetched data in {:.2f} ms.".format(1000 * (_t - t))
                    )
                    await ctx.send(
                        embed = em,
                        file = discord.File(
                            io.BytesIO(data),
                            filename = "audio.mp3",
                        )
                    )
