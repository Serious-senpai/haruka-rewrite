import discord

from core import bot


@bot.event
async def on_message_delete(message: discord.Message):
    if isinstance(message.channel, discord.TextChannel) and not message.author.id == bot.user.id:
        await bot.conn.execute(f"DELETE FROM snipe WHERE channel_id = '{message.channel.id}';")
        await bot.conn.execute(
            f"INSERT INTO snipe VALUES ('{message.channel.id}', '{message.id}', $1, '{message.author.id}', $2);",
            message.content, [attachment.proxy_url for attachment in message.attachments],
        )
