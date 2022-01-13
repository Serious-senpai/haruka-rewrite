import discord

from core import bot


@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    if isinstance(message.channel, (discord.DMChannel, discord.TextChannel)):
        await bot.process_commands(message)
