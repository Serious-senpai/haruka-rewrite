import discord
from discord.ext import commands
from discord.utils import escape_markdown as escape

import cards
from core import bot


CARD_LIMIT: int = 9


@bot.command(
    name="card",
    description="Draw a number of cards from the 52-card standard deck",
    usage="card <amount | default: 1>",
)
@commands.cooldown(1, 3, commands.BucketType.user)
async def _card_cmd(ctx: commands.Context, n: int = 1):
    if n < 1 or n > CARD_LIMIT:
        return await ctx.send(f"Invalid card number (must be from 1 to {CARD_LIMIT}).")

    hand: cards.BaseHand = cards.BaseHand()
    for _ in range(n):
        hand.draw()

    file: discord.File = discord.File(hand.make_image(), filename="image.png")
    embed: discord.Embed = discord.Embed(title=f"{escape(ctx.author.name)} drew {n} card(s)!")
    embed.set_image(url="attachment://image.png")
    embed.set_footer(text=f"Total points: {hand.value}")

    await ctx.send(
        file=file,
        embed=embed,
    )
