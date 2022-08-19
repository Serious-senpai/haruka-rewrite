from discord.ext import commands

from _types import Context
from core import bot
from env import HOST
from web.routes import audio


@bot.command(
    name="register",
    description="Register the current voice client to be able to control via the web browser",
)
@commands.guild_only()
@commands.cooldown(1, 2, commands.BucketType.user)
async def _register_cmd(ctx: Context):
    client = ctx.voice_client
    if client and client.is_connected():
        key = audio.voice_manager.push(client)
        url = HOST + f"/audio-control?key={key}"
        await ctx.send(f"You can now control the music player via {url}")

    else:
        await ctx.send("No currently connected player.")
