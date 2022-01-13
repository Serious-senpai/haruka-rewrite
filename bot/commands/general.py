import datetime
import inspect
from typing import List, Optional, Tuple

import discord
from discord.ext import commands
from discord.utils import escape_markdown as escape

import info
import emoji_ui
import utils
from core import bot, prefix


@bot.command(
    name="about",
    description="Display bot information",
)
@commands.cooldown(1, 2, commands.BucketType.user)
async def _about_cmd(ctx: commands.Context):
    embed: discord.Embed = info.user_info(bot.user)
    embed.description += "\nIf you are too bored, [vote](https://top.gg/bot/848178172536946708/vote) for me on top.gg!"
    embed.add_field(
        name="Latest commits from the `main` branch",
        value=bot.latest_commits,
        inline=False,
    )
    embed.add_field(
        name="Uptime",
        value=datetime.datetime.now() - bot.uptime,
    )
    embed.add_field(
        name="Latency",
        value=utils.format(bot.latency),
    )
    embed.add_field(
        name="Links",
        value=f"[Top.gg](https://top.gg/bot/848178172536946708)\n[GitHub](https://github.com/Saratoga-CV6/haruka-rewrite)\n[Website]({bot.HOST})",
    )
    await ctx.send(embed=embed)


@bot.command(
    name="info",
    description="Get information about a user or yourself",
    usage="info\ninfo <user>",
)
@commands.guild_only()
@commands.cooldown(1, 2, commands.BucketType.user)
async def _info_cmd(ctx: commands.Context, *, user: discord.User = None):
    if user is None:
        user = ctx.author
    info_em: discord.Embed = info.user_info(user)
    info_em.set_author(
        name="Information collected",
        icon_url=bot.user.avatar.url,
    )
    await ctx.send(embed=info_em)


@bot.command(
    name="ping",
    description="Measure the bot's latency",
)
@commands.cooldown(1, 10, commands.BucketType.user)
async def _ping_cmd(ctx: commands.Context):
    with utils.TimingContextManager() as measure:
        message: discord.Message = await ctx.send("🏓 **Ping!**")
    await message.edit(f"🏓 **Pong!** in {utils.format(measure.result)} (average {utils.format(bot.latency)})")


@bot.command(
    name="prefix",
    description="View or change the bot's prefix in this server.\nThis requires the `Manage Server` permission.",
    usage="prefix\nprefix <prefix>",
)
@commands.guild_only()
@commands.cooldown(1, 2, commands.BucketType.guild)
async def _prefix_cmd(ctx: commands.Context, *, pref: str = None):
    if not pref:
        p: str = await prefix(bot, ctx.message)
        return await ctx.send(f"The current prefix is `{p}`")

    if not ctx.channel.permissions_for(ctx.author).manage_guild:
        raise commands.MissingPermissions("manage_guild")

    if " " in pref:
        return await ctx.send("Prefix must not contain any spaces!")

    id: int = ctx.guild.id
    await bot.conn.execute(f"DELETE FROM prefix WHERE id = '{id}' OR pref = '$';")
    if not pref == "$":
        await bot.conn.execute(f"INSERT INTO prefix VALUES ('{id}', $1);", pref)

    await ctx.send(f"Prefix has been set to `{pref}`")


@bot.command(
    name="say",
    description="Make me say something. I can also copy your attachments!",
    usage="say <anything>"
)
@commands.cooldown(1, 1, commands.BucketType.user)
async def _say_cmd(ctx: commands.Context, *, content: str):
    files: List[discord.File] = []
    for attachment in ctx.message.attachments:
        files.append(await attachment.to_file())
    await ctx.send(content, files=files, reference=ctx.message.reference)


@bot.command(
    name="avatar",
    aliases=["ava"],
    description="Get an avatar from a user",
    usage="avatar <user | default: yourself>",
)
@commands.cooldown(1, 2, commands.BucketType.user)
async def _avatar_cmd(ctx: commands.Context, *, user: discord.User = None):
    if user is None:
        user = ctx.author
    if not user.avatar:
        return await ctx.send("This user hasn't uploaded an avatar yet.")
    ava_em: discord.Embed = discord.Embed()
    ava_em.set_author(
        name=f"This is {user.name}'s avatar",
        icon_url=bot.user.avatar.url,
    )
    ava_em.set_image(url=user.avatar.url)
    await ctx.send(embed=ava_em)


@bot.command(
    name="svinfo",
    description="Retrieve information about this server",
)
@commands.guild_only()
@commands.cooldown(1, 2, commands.BucketType.user)
async def _svinfo_cmd(ctx: commands.Context):
    sv_em = info.server_info(ctx.guild)
    await ctx.send(embed=sv_em)


@bot.command(
    name="emoji",
    aliases=["emojis"],
    description="Show all emojis from the server",
)
@commands.guild_only()
@commands.cooldown(1, 2, commands.BucketType.user)
async def _emoji_cmd(ctx: commands.Context):
    emojis: Tuple[discord.Emoji, ...] = ctx.guild.emojis
    pages: int = 1 + int(len(emojis) / 50)
    index: List[discord.Embed] = []
    for page in range(pages):
        embed: discord.Embed = discord.Embed(
            title=escape(ctx.guild.name),
            description="".join(f"<a:{emoji.name}:{emoji.id}>" if emoji.animated else f"<:{emoji.name}:{emoji.id}>" for emoji in emojis[page * 50:page * 50 + 50]),
        )
        embed.set_author(
            name="These are the server's emojis!",
            icon_url=ctx.author.avatar.url if ctx.author.avatar else discord.Embed.Empty,
        )
        embed.set_thumbnail(url=ctx.guild.icon.url if ctx.guild.icon else discord.Embed.Empty)
        embed.set_footer(text=f"Showing page {page + 1}/{pages}")
        index.append(embed)
    display: emoji_ui.Pagination = emoji_ui.Pagination(index)
    await display.send(ctx.channel)


@bot.command(
    name="remind",
    description="Remind you about something via DM.\nThe `content` is your reminder note.\nExample: `remind 0 30 do homework` will remind you to do your homework after 30 minutes.",
    usage="remind <hours> <minutes> <content>",
)
@commands.cooldown(1, 2, commands.BucketType.user)
async def _remind_cmd(ctx: commands.Context, hours: int, minutes: int, *, content: str):
    if hours < 0 or minutes < 0:
        return await ctx.send("Both `hours` and `minutes` must be greater than or equal to 0.")

    if hours == 0 and minutes == 0:
        return await ctx.send("Specified time must be greater than 0.")

    if len(content) > 1000:
        return await ctx.send("Maximum length for `content` is 1000 characters.")

    now: datetime.datetime = discord.utils.utcnow()
    time: datetime.datetime = now + datetime.timedelta(hours=hours, minutes=minutes)

    await bot.conn.execute(
        f"INSERT INTO remind VALUES ('{ctx.author.id}', $1, $2, $3, $4);",
        time, content, ctx.message.jump_url, now,
    )
    bot.task.remind.restart()

    embed: discord.Embed = discord.Embed()
    embed.add_field(
        name="Content",
        value=content,
        inline=False,
    )
    embed.add_field(
        name="After",
        value=f"{hours}h {minutes}m",
        inline=False,
    )
    embed.set_author(
        name="Created new reminder",
        icon_url=ctx.author.avatar.url if ctx.author.avatar else discord.Embed.Empty,
    )
    embed.set_thumbnail(url=bot.user.avatar.url)
    embed.set_footer(text="Make sure you can receive Direct Message from me")
    await ctx.send(embed=embed)


@bot.command(
    name="source",
    description="Get the source code of a command",
    usage="source <command name>",
)
@commands.cooldown(1, 2, commands.BucketType.user)
async def _source_cmd(ctx: commands.Context, *, cmd: str):
    if cmd.lower() == "help":
        file: discord.File = discord.File("./bot/commands/help.py", filename="source.py")
    elif cmd.startswith("*"):
        file: discord.File = discord.File("./bot/image.py", filename="source.py")
    else:
        command: Optional[commands.Command] = bot.get_command(cmd)
        if not command:
            return await ctx.send(f"No command named `{cmd}` was found.")

        source: str = inspect.getsource(command.callback)
        with open("./source.py", "w", encoding="utf-8") as f:
            f.write(source)

        file: discord.File = discord.File("./source.py")

    await ctx.send("This is the source code", file=file)
