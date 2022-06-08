from typing import Optional

import discord
from discord.ext import commands

from _types import Context
from core import bot
from lib import emoji_ui, saucenao


async def _send_single_sauce(target: discord.abc.Messageable, image_url: str) -> None:
    results = await saucenao.SauceResult.get_sauce(image_url, session=bot.session)
    if not results:
        return await target.send("Cannot find the image sauce!")

    total = len(results)
    embeds = []
    for index, result in enumerate(results):
        embed = result.create_embed()
        embed.set_author(
            name="Image search result",
            icon_url=bot.user.avatar.url,
        )
        embed.set_footer(text=f"Displaying result {index + 1}/{total}")
        embeds.append(embed)

    display = emoji_ui.NavigatorPagination(bot, embeds)
    await display.send(target)


@bot.command(
    name="sauce",
    description="Find the image source with saucenao.",
    usage="sauce <URL to image>\nsauce <attachment>",
)
@commands.cooldown(1, 2, commands.BucketType.user)
async def _sauce_cmd(ctx: Context, image_url: Optional[str] = None):
    if image_url is None and not ctx.message.attachments:
        raise commands.UserInputError

    if image_url is not None:
        return await _send_single_sauce(ctx.channel, image_url)

    embeds = []
    image_total = len(ctx.message.attachments)
    if image_total == 1:
        return await _send_single_sauce(ctx.channel, ctx.message.attachments[0].url)

    breakpoints = []
    for image_index, attachment in enumerate(ctx.message.attachments):
        results = await saucenao.SauceResult.get_sauce(attachment.url, session=bot.session)
        result_total = len(results)
        if result_total > 0:
            breakpoints.append(len(embeds))

        for result_index, result in enumerate(results):
            embed = result.create_embed()
            embed.set_author(
                name="Image search result",
                icon_url=bot.user.avatar.url,
            )
            embed.set_footer(text=f"Displaying result {result_index + 1}/{result_total} (image {image_index + 1}/{image_total})")
            embeds.append(embed)

    if embeds:
        display = emoji_ui.StackedNavigatorPagination(bot, embeds, breakpoints)
        await display.send(ctx.channel)
    else:
        await ctx.send("Cannot find the sauce for any of the images provided!")
