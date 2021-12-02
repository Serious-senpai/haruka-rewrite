import datetime
from typing import List, Optional

import asyncpg
import discord
from discord.ext import commands

from core import bot


MUTED_PERM: discord.Permissions = discord.Permissions.none()
MUTED_PERM.read_messages = True
MUTED_PERM.read_message_history = True
MUTED_PERM.add_reactions = True


@bot.command(
    name = "mute",
    description = "Mute a member for a period of time. This member will be removed all existing roles and assigned `Muted by Haruka`.\nAfter the muting period, the removed roles will be assigned back.",
    usage = "mute <hours> <minutes> <member> <reason>",
)
@commands.guild_only()
@commands.bot_has_guild_permissions(manage_roles = True)
@commands.has_guild_permissions(manage_guild = True)
@commands.cooldown(1, 4, commands.BucketType.user)
async def _mute_cmd(ctx: commands.Context, hours: int, minutes: int, member: discord.Member, *, reason: str = "*No reason given*"):
    if hours < 0 or minutes < 0:
        return await ctx.send("Both `hours` and `minutes` must be greater than or equal to 0.")

    if hours == 0 and minutes == 0:
        return await ctx.send("Specified time must be greater than 0.")

    row: Optional[asyncpg.Record] = await bot.conn.fetchrow(f"SELECT * FROM muted WHERE member = '{member.id}' AND guild = '{ctx.guild.id}';")
    if row:
        return await ctx.send("This member has already been muted!")

    if ctx.guild.default_role.permissions.send_messages:
        return await ctx.send("The `@everyone` role in this server can still send messages so it is impossible to mute someone.\nPlease edit the server settings first.")

    role: Optional[discord.Role] = discord.utils.find(lambda r: r.name == "Muted by Haruka", ctx.guild.roles)
    if not role:
        try:
            role = await ctx.guild.create_role(
                name = "Muted by Haruka",
                permissions = MUTED_PERM,
                reason = "Create role for muted members",
            )
        except:
            return await ctx.send("Cannot create the mute role. Operation failed.\nMake sure that I have the proper permissions!")

    now: datetime.datetime = discord.utils.utcnow()
    time: datetime.datetime = now + datetime.timedelta(hours = hours, minutes = minutes)
    current_roles: List[discord.Role] = member.roles[1:]

    await bot.conn.execute(
        f"INSERT INTO muted VALUES ('{member.id}', '{ctx.guild.id}', $1, $2);",
        time, [str(role.id) for role in member.roles[1:]],
    )
    bot.task.unmute.restart()

    try:
        await member.add_roles(role)
    except:
        return await ctx.send("Unable to mute this member.")

    warning: bool = False
    try:
        await member.remove_roles(*current_roles, reason = "Mute: " + reason[:50])
    except:
        warning = True

    em: discord.Embed = discord.Embed(
        description = "Cannot remove all roles, this member may not be muted completely." if warning else discord.Embed.Empty,
        color = 0x2ECC71,
        timestamp = discord.utils.utcnow(),
    )
    em.set_author(
        name = f"{ctx.author.name} muted 1 member",
        icon_url = ctx.author.avatar.url if ctx.author.avatar else discord.Embed.Empty,
    )
    em.add_field(
        name = "Muted",
        value = member,
    )
    em.add_field(
        name = "Duration",
        value = f"{hours}h {minutes}m",
    )
    em.add_field(
        name = "Reason",
        value = reason,
        inline = False,
    )
    em.set_thumbnail(url = member.avatar.url if member.avatar else discord.Embed.Empty)
    await ctx.send(embed = em)
