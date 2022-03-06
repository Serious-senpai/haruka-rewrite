import datetime

import discord
from discord.ext import commands

from _types import Context
from core import bot


@bot.command(
    name="mute",
    description="Mute a member for a period of time.",
    usage="mute <hours> <minutes> <member> <reason>",
)
@commands.guild_only()
@commands.bot_has_guild_permissions(moderate_members=True)
@commands.has_guild_permissions(moderate_members=True)
@commands.cooldown(1, 2, commands.BucketType.user)
async def _mute_cmd(ctx: Context, hours: int, minutes: int, member: discord.Member, *, reason: str = None):
    if hours < 0 or minutes < 0:
        return await ctx.send("Both `hours` and `minutes` must be greater than or equal to 0.")

    if hours == 0 and minutes == 0:
        return await ctx.send("Specified time must be greater than 0.")

    target = discord.utils.utcnow() + datetime.timedelta(seconds=3600 * hours + 60 * minutes)
    try:
        await member.edit(timed_out_until=target, reason=reason)
    except discord.Forbidden:
        return await ctx.send("Cannot mute this member, most likely due to a higher role.")

    if reason is None:
        reason = "*No reason given*"

    embed = discord.Embed()
    embed.set_author(
        name="Muted 1 member",
        icon_url=ctx.author.avatar.url if ctx.author.avatar else discord.Embed.Empty,
    )
    embed.add_field(
        name="Muted member",
        value=member,
    )
    embed.add_field(
        name="Duration",
        value=f"{hours}h {minutes}m",
    )
    embed.add_field(name="Reason", value=reason, inline=False)
    embed.set_thumbnail(url=member.avatar.url if member.avatar else discord.Embed.Empty)
    await ctx.send(embed=embed, reference=ctx.message.reference)
