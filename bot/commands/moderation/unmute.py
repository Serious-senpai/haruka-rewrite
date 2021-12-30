from typing import Optional

import asyncpg
import discord
from discord.ext import commands

import utils
from core import bot


@bot.command(
    name="unmute",
    description="Unmute a muted member.",
    usage="unmute <member> <reason>",
)
@commands.guild_only()
@commands.bot_has_guild_permissions(manage_roles=True)
@commands.has_guild_permissions(manage_guild=True)
@commands.cooldown(1, 2, commands.BucketType.user)
async def _unmute_cmd(ctx: commands.Context, member: discord.Member, *, reason: str = "*No reason given*"):
    row: Optional[asyncpg.Record] = await bot.conn.fetchrow(f"SELECT * FROM muted WHERE member = '{member.id}' AND guild = '{ctx.guild.id}';")

    if not row:
        return await ctx.send("This member wasn't muted!")

    await bot.task.unmute.unmute(row, member=member, reason=reason)

    em: discord.Embed = discord.Embed()
    em.set_author(
        name=f"{ctx.author.name} unmuted 1 member",
        icon_url=ctx.author.avatar.url if ctx.author.avatar else discord.Embed.Empty,
    )
    em.add_field(
        name="Member",
        value=str(member),
    )
    em.add_field(
        name="Reason",
        value=reason,
        inline=False,
    )
    em.set_thumbnail(url=member.avatar.url if member.avatar else discord.Embed.Empty)
    await ctx.send(embed=em, reference=utils.get_reply(ctx.message))
