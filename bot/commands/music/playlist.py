from typing import Optional
from urllib import parse

import discord
from discord.ext import commands

import audio
import _playlist
from core import bot


@bot.command(
    name="playlist",
    description="Load a public playlist from YouTube into the voice channel.",
    usage="playlist <playlist ID>\nplaylist <youtube URL>",
)
@audio.in_voice()
@commands.cooldown(1, 2, commands.BucketType.user)
async def _playlist_cmd(ctx: commands.Context, *, url: str):
    channel: discord.VoiceChannel = ctx.author.voice.channel

    try:
        query: str = parse.urlparse(url).query
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
