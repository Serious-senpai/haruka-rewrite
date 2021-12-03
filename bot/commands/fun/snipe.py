import datetime
from typing import List, Optional

import asyncpg
import discord
from discord.ext import commands

from core import bot


class SnipedMessage:

    __slots__ = (
        "content",
        "id",
        "author_id",
        "attachments",
    )

    def __init__(self, row: asyncpg.Record):
        self.content: Optional[str] = row["content"]
        self.id: int = int(row["message_id"])
        self.author_id: int = int(row["author_id"])
        self.attachments: List[str] = row["attachments"]

    @property
    def created_at(self) -> datetime.datetime:
        return discord.utils.snowflake_time(self.id)


@bot.command(
    name="snipe",
    description="Get a deleted messge in the channel.\nNote that I cannot snipe my own messages!",
)
@commands.guild_only()
@commands.cooldown(1, 4, commands.BucketType.user)
async def _snipe_cmd(ctx: commands.Context):
    row: Optional[asyncpg.Record] = await bot.conn.fetchrow(f"SELECT * FROM snipe WHERE channel_id = '{ctx.channel.id}';")
    if not row:
        return await ctx.send("Cannot snipe any messages!")

    message: SnipedMessage = SnipedMessage(row)
    em: discord.Embed = discord.Embed(
        color=0x2ECC71,
        timestamp=message.created_at,
    )

    author: discord.User = await bot.fetch_user(message.author_id)
    em.set_author(
        name=f"From {author.name}",
        icon_url=author.avatar.url if author.avatar else discord.Embed.Empty,
    )

    if message.content:
        em.add_field(
            name="Content",
            value=message.content,
            inline=False,
        )

    urls: str = "\n".join(message.attachments)
    if urls:
        em.add_field(
            name="Attachment",
            value=urls,
            inline=False,
        )
        em.set_image(url=message.attachments[0])

    await ctx.send(embed=em)
