import discord
from discord import app_commands

from _types import Interaction
from core import bot
from lib import cards


CARD_LIMIT = 9


@bot.slash(
    name="card",
    description="Draw a number of cards from the 52-card standard deck",
)
@app_commands.describe(count="The number of cards to draw, default to 1")
async def _card_slash(interaction: Interaction, count: int = 1):
    if count < 1 or count > CARD_LIMIT:
        return await interaction.response.send_message(f"Invalid card number (must be from 1 to {CARD_LIMIT}).")

    await interaction.response.defer()
    hand = cards.CardHand()
    hand.draw(cards.BaseCard, count=count)
    hand.sort()

    file = discord.File(hand.to_image_data(), filename="image.png")
    embed = discord.Embed()
    embed.set_author(
        name=f"{interaction.user.name} drew {count} card(s)!",
        icon_url=interaction.user.avatar.url if interaction.user.avatar else None,
    )
    embed.set_image(url="attachment://image.png")
    embed.set_footer(text=f"Total points: {hand.value}. Streak: {hand.streak}")

    await interaction.followup.send(file=file, embed=embed)
