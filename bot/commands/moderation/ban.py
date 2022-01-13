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

    em = discord.Embed()

    if success:
        em.add_field(
            name="Banned",
            value=", ".join(f"<@!{user.id}>" for user in success),
            inline=False,
        )

    if fail:
        em.add_field(
            name="Unable to ban",
            value=", ".join(f"<@!{user.id}>" for user in fail),
            inline=False,
        )
        em.set_footer(text="Please assign me an appropriate role.")

    if len(success) == 1:
        em.set_author(
            name="Banned 1 member",
            icon_url=ctx.author.avatar.url if ctx.author.avatar else discord.Embed.Empty,
        )
    else:
        em.set_author(
            name=f"Banned {len(success)} members",
            icon_url=ctx.author.avatar.url if ctx.author.avatar else discord.Embed.Empty,
        )

    em.add_field(
        name="Reason",
        value=reason,
        inline=False,
    )
    em.set_thumbnail(url=ctx.guild.icon.url if ctx.guild.icon else discord.Embed.Empty)

    await ctx.send(embed=em, reference=ctx.message.reference)
