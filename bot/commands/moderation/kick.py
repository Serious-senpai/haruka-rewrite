import discord
from discord.ext import commands

from _types import Context
from core import bot


@bot.command(
    name="kick",
    description="Kick a user(s) from the server.",
    usage="kick <user(s)> <reason>",
)
@commands.guild_only()
@commands.bot_has_guild_permissions(kick_members=True)
@commands.has_guild_permissions(kick_members=True)
@commands.cooldown(1, 2, commands.BucketType.user)
async def _kick_cmd(ctx: Context, users: commands.Greedy[discord.Object], *, reason: str = "*No reason given*"):
    if not users:
        raise commands.UserInputError

    success = []
    fail = []
    for user in users:
        try:
            await ctx.guild.kick(user, reason=reason)
        except BaseException:
            fail.append(user)
        else:
            success.append(user)

    embed = discord.Embed()

    if success:
        embed.add_field(
            name="Kicked",
            value=", ".join(f"<@!{user.id}>" for user in success),
            inline=False,
        )

    if fail:
        embed.add_field(
            name="Unable to kick",
            value=", ".join(f"<@!{user.id}>" for user in fail),
            inline=False,
        )
        embed.set_footer(text="Please assign me an appropriate role.")

    if len(success) == 1:
        embed.set_author(
            name="Kicked 1 member",
            icon_url=ctx.author.avatar.url if ctx.author.avatar else None,
        )
    else:
        embed.set_author(
            name=f"Kicked {len(success)} members",
            icon_url=ctx.author.avatar.url if ctx.author.avatar else None,
        )

    embed.add_field(name="Reason", value=reason, inline=False)
    embed.set_thumbnail(url=ctx.guild.icon.url if ctx.guild.icon else None)

    await ctx.send(embed=embed, reference=ctx.message.reference)
