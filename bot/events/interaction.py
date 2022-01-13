import discord

from core import bot


@bot.event
async def on_interaction(interaction: discord.Interaction):
    if interaction.type == discord.InteractionType.application_command:
        """Execute slash commands"""
        row = await bot.conn.fetchrow(f"SELECT * FROM blacklist WHERE id = '{interaction.user.id}';")
        if row is not None:
            return await interaction.response.send_message("You are currently in the blacklist.", ephemeral=True)

        await bot.process_slash_commands(interaction)
