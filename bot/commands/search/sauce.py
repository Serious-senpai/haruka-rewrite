from typing import List, Optional

import discord
from discord.ext import commands

import emoji_ui
from leech import get_sauce
from core import bot


@bot.command(
    name="sauce",
    description="Find the image source with saucenao.",
    usage="sauce <URL to image>\nsauce <attachment>",
)
@commands.cooldown(1, 2, commands.BucketType.user)
async def _sauce_cmd(ctx: commands.Context, src: Optional[str] = None):
    if src is None:
        try:
            src = ctx.message.attachments[0].url
        except IndexError:
            raise commands.UserInputError

    results: List[discord.Embed] = await get_sauce(src)

    if len(results) > 0:
        display: emoji_ui.Pagination = emoji_ui.Pagination(results)
        await display.send(ctx)
    else:
        await ctx.send("Cannot find the image sauce")
