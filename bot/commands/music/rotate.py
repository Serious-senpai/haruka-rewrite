from discord.ext import commands

import audio
from _types import Context
from core import bot


@bot.command(
    name="rotate",
    description="Rotate the music queue so that the song at the specified index becomes the first.\nExample: `rotate 3`: `1 2 3 4 5 6` -> `3 4 5 6 1 2`",
    usage="rotate <index>",
)
@audio.in_voice()
@commands.cooldown(1, 2, commands.BucketType.user)
async def _rotate_cmd(ctx: Context, index: int):
    channel_id = ctx.author.voice.channel.id
    queue = await audio.MusicClient.queue(channel_id)
    length = len(queue)

    if length == 0:
        return await ctx.send("Please add a song to the queue first!")

    if index < 1 or index > length:
        return await ctx.send(f"Invalid `index` argument (must be from `1` to `{length}`)")

    n = index - 1
    queue = queue[n:] + queue[:n]
    await bot.conn.execute(f"UPDATE youtube SET queue = $1 WHERE id = '{channel_id}';", queue)
    await ctx.send(f"Rotated song at index `{index}` to the first")
