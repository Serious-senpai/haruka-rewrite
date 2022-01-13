from typing import Optional

import asyncpg
import discord
from discord.ext import commands

from core import bot


@bot.command(
    name="unmute",
    description="Unmute a muted member.",
    usage="unmute <member> <reason>",
)
@commands.guild_only()
@commands.bot_has_guild_permissions(manage_members=True)
@commands.has_guild_permissions(manage_members=True)
@commands.cooldown(1, 2, commands.BucketType.user)
async def _unmute_cmd(ctx: commands.Context, member: discord.Member, *, reason: str = None):
    try:
        await member.edit(timed_out_until=None, reason=reason)
    except discord.HTTPException:
        return await ctx.send("Cannot unmute this member!")

    if reason is None:
        reason = "*No reason given*"

    embed = discord.Embed()
    embed.set_author(
        name=f"{ctx.author.name} unmuted 1 member",
        icon_url=ctx.author.avatar.url if ctx.author.avatar else discord.Embed.Empty,
    )
    embed.add_field(
        name="Unmuted member",
        value=member,
    )
    embed.add_field(
        name="Reason",
        value=reason,
        inline=False,
    )
    embed.set_thumbnail(url=member.avatar.url if member.avatar else discord.Embed.Empty)
    await ctx.send(embed=embed, reference=ctx.message.reference)
