from _types import Interaction
from core import bot


@bot.listen()
async def on_interaction(interaction: Interaction):
    guild_id = interaction.guild_id
    if guild_id is not None:
        await bot.reset_inactivity_counter(guild_id)
