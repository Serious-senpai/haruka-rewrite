import json

from discord.ext import commands

import audio
from _types import Context
from core import bot


@bot.command(
    name="import",
    description="Import a music queue from a file. Note that the old queue of the voice channel will be overwritten.\nSee also: the `export` command.",
)
@audio.in_voice()
@commands.cooldown(1, 2, commands.BucketType.user)
async def _import_cmd(ctx: Context):
    channel = ctx.author.voice.channel
    try:
        data = await ctx.message.attachments[0].read()
        queue = json.loads(data)
    except IndexError:
        return await ctx.send("Please attach a file containing the music queue data to the message")
    except json.JSONDecodeError:
        return await ctx.send("Invalid data has been provided. Please try another one.")

    length = len(queue)
    if length == 0:
        return await ctx.send("The provided data represents an empty queue. Please try another one.")

    await bot.conn.execute(f"DELETE FROM youtube WHERE id = '{channel.id}';")
    await bot.conn.execute(f"INSERT INTO youtube VALUES ('{channel.id}', $1);", queue)

    if length == 1:
        await ctx.send(f"Loaded a track into <#{channel.id}>")
    else:
        await ctx.send(f"Loaded {length} tracks into <#{channel.id}>")
