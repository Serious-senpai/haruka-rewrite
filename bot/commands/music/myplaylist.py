from typing import List

import asyncpg
import discord
from discord.ext import commands

import _playlist
import emoji_ui
from core import bot


@bot.command(
    name="myplaylist",
    aliases=["myplaylists"],
    description="View your published playlists",
)
@commands.cooldown(1, 2, commands.BucketType.user)
async def _myplaylist_cmd(ctx: commands.Context):
    rows: List[asyncpg.Record] = await bot.conn.fetch(f"SELECT * FROM playlist WHERE author_id = '{ctx.author.id}' LIMIT 10;")
    playlists: List[_playlist.Playlist] = [_playlist.Playlist(row, ctx.author) for row in rows]
    length: int = len(playlists)
    embeds: List[discord.Embed] = []

    embed: discord.Embed
    for index, playlist in enumerate(playlists):
        embed = playlist.create_embed()
        embed.set_author(
            name=f"Displaying playlist #{index + 1}",
            icon_url=bot.user.avatar.url,
        )
        embed.set_footer(text=f"Playlist {index + 1}/{length}")
        embeds.append(embed)

    display: emoji_ui.NavigatorPagination = emoji_ui.NavigatorPagination(embeds)
    await display.send(ctx)
