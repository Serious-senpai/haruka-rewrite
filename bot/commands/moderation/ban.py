from typing import List

import discord
from discord.ext import commands

from core import bot


@bot.command(
    name="ban",
    description="Ban a user(s) from the server.",
    usage="ban <user(s)> <reason>",
)
@commands.guild_only()
@commands.bot_has_guild_permissions(ban_members=True)
@commands.has_guild_permissions(ban_members=True)
@commands.cooldown(1, 2, commands.BucketType.user)
async def _ban_cmd(ctx: commands.Context, users: commands.Greedy[discord.Object], *, reason: str = "*No reason given*"):
    if not users:
        raise commands.UserInputError

    success = []
    fail = []
    for user in users:
        try:
            await ctx.guild.ban(user, reason=reason, delete_message_days=0)
        except BaseException:
            fail.append(user)
        else:
            success.append(user)

    embed = discord.Embed()

    if success:
        embed.add_field(
            name="Banned",
            value=", ".join(f"<@!{user.id}>" for user in success),
            inline=False,
        )

    if fail:
        embed.add_field(
            name="Unable to ban",
            value=", ".join(f"<@!{user.id}>" for user in fail),
            inline=False,
        )
        embed.set_footer(text="Please assign me an appropriate role.")

    if len(success) == 1:
        embed.set_author(
            name="Banned 1 member",
            icon_url=ctx.author.avatar.url if ctx.author.avatar else discord.Embed.Empty,
        )
    else:
        embed.set_author(
            name=f"Banned {len(success)} members",
            icon_url=ctx.author.avatar.url if ctx.author.avatar else discord.Embed.Empty,
        )

    embed.add_field(
        name="Reason",
        value=reason,
        inline=False,
    )
    embed.set_thumbnail(url=ctx.guild.icon.url if ctx.guild.icon else discord.Embed.Empty)

    await ctx.send(embed=embed, reference=ctx.message.reference)
