from typing import Optional, Union
from urllib import parse

import discord
from discord.ext import commands

import _playlist
from core import bot


@bot.command(
    name="playlist",
    description="Load a playlist from the bot's playlist dashboard or YouTube into the voice channel.",
    usage="playlist <playlist ID>\nplaylist <youtube URL>",
)
@commands.guild_only()
@commands.cooldown(1, 2, commands.BucketType.user)
async def _playlist_cmd(ctx: commands.Context, id: Union[int, str]):
    if not ctx.author.voice:
        return await ctx.send("Please join a voice channel first.")

    channel: discord.abc.Connectable = ctx.author.voice.channel

    if isinstance(id, int):
        result: Optional[_playlist.Playlist] = await _playlist.Playlist.get(bot, id)
        if not result:
            return await ctx.send(f"No playlist with ID `{id}`")

        await bot.conn.execute(f"DELETE FROM youtube WHERE id = '{channel.id}';")
        await bot.conn.execute(f"INSERT INTO youtube VALUES('{channel.id}', $1);", result.queue)
        await bot.conn.execute("UPDATE playlist SET use_count = use_count + 1 WHERE id = $1", id)

        embed: discord.Embed = result.create_embed()
        embed.set_author(
            name=f"{ctx.author.name} loaded a public playlist into {channel.name}",
            icon_url=ctx.author.avatar.url if ctx.author.avatar else discord.Embed.Empty,
        )
        await ctx.send(embed=embed)

    else:
        try:
            query: str = parse.urlparse(id).query
            playlist_id: str = parse.parse_qs(query)["list"][0]
        except BaseException:
            raise commands.UserInputError
        else:
            result: Optional[_playlist.YouTubePlaylist] = await _playlist.YouTubePlaylist.get(bot, playlist_id)
            if not result:
                return await ctx.send("Cannot find this playlist. Make sure that this playlist isn't private.")

            await result.load(bot.conn, channel.id)
            embed: discord.Embed = result.create_embed()
            embed.set_author(
                name=f"{ctx.author.name} loaded a YouTube playlist into {channel.name}",
                icon_url=ctx.author.avatar.url if ctx.author.avatar else discord.Embed.Empty,
            )
            await ctx.send(embed=embed)
