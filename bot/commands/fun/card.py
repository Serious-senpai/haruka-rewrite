import discord
from discord.ext import commands

from _types import Context
from core import bot
from lib import cards


CARD_LIMIT = 9


@bot.command(
    name="card",
    aliases=["cards"],
    description="Draw a number of cards from the 52-card standard deck",
    usage="card <amount | default: 1>",
)
@commands.cooldown(1, 3, commands.BucketType.user)
async def _card_cmd(ctx: Context, cards_count: int = 1):
    if cards_count < 1 or cards_count > CARD_LIMIT:
        return await ctx.send(f"Invalid card number (must be from 1 to {CARD_LIMIT}).")

    hand = cards.CardHand()
    hand.draw(cards.BaseCard, count=cards_count)
    hand.sort()

    file = discord.File(hand.to_image_data(), filename="image.png")
    embed = discord.Embed()
    embed.set_author(
        name=f"{ctx.author.name} drew {cards_count} card(s)!",
        icon_url=ctx.author.avatar.url if ctx.author.avatar else None,
    )
    embed.set_image(url="attachment://image.png")
    embed.set_footer(text=f"Total points: {hand.value}. Streak: {hand.streak}")

    await ctx.send(file=file, embed=embed)
