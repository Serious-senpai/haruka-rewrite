import yarl
from discord.ext import commands

from _types import Context
from core import bot
from lib import emoji_ui, playlist


@bot.command(
    name="playlist",
    description="Load a public playlist/mix from YouTube into the voice channel.",
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
        result = await playlist.get(playlist_id, session=bot.session)
        if not result:
            return await ctx.send("Cannot find this playlist. Please make sure that this playlist isn't private.")

        queue = await bot.audio.queue(channel.id)
        if queue:
            message = await ctx.send(f"{len(queue)} songs in <#{channel.id}> will be replaced with {len(result.videos)} in the playlist. Are you sure?")
            display = emoji_ui.YesNoSelection(bot, message)
            choice = await display.listen(ctx.author.id)
            if choice is None:
                return

            if choice is False:
                return await ctx.send("Request cancelled.")

        await result.load(channel.id, conn=bot.conn)
        embed = result.create_embed()
        embed.set_author(
            name=f"{ctx.author.name} loaded a YouTube playlist into {channel.name}",
            icon_url=ctx.author.avatar.url if ctx.author.avatar else None,
        )
        await ctx.send(embed=embed)
