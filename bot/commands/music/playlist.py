import yarl
from discord.ext import commands

from _types import Context
from core import bot
from lib import playlist


@bot.command(
    name="playlist",
    description="Load a public playlist from YouTube into the voice channel.",
    usage="playlist <playlist ID>\nplaylist <youtube URL>",
)
@bot.audio.in_voice()
@commands.cooldown(1, 2, commands.BucketType.user)
async def _playlist_cmd(ctx: Context, *, url: str):
    channel = ctx.author.voice.channel

    try:
        playlist_id = yarl.URL(url).query["list"]
    except BaseException:
        raise commands.UserInputError
    else:
        result = await playlist.YouTubePlaylist.get(bot, playlist_id)
        if not result:
            return await ctx.send("Cannot find this playlist. Make sure that this playlist isn't private.")

        await result.load(bot.conn, channel.id)
        embed = result.create_embed()
        embed.set_author(
            name=f"{ctx.author.name} loaded a YouTube playlist into {channel.name}",
            icon_url=ctx.author.avatar.url if ctx.author.avatar else None,
        )
        await ctx.send(embed=embed)
