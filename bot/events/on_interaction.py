from typing import List

import asyncpg
import discord

from core import bot


@bot.event
async def on_interaction(interaction: discord.Interaction):
    if interaction.type == discord.InteractionType.application_command:
        """Execute slash commands"""
        row: asyncpg.Record = await bot.conn.fetchrow("SELECT * FROM misc WHERE title = 'blacklist';")
        blacklist_ids: List[str] = row["id"]

        if str(interaction.user.id) in blacklist_ids:
            return await interaction.response.send_message("You are currently in the blacklist.", ephemeral=True)

        await bot.process_slash_commands(interaction)
