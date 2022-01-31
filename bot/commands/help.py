from __future__ import annotations

from typing import List, Mapping, Optional, TYPE_CHECKING

import discord
from discord.ext import commands

import utils
import emoji_ui
from core import bot, prefix
if TYPE_CHECKING:
    import haruka


IGNORE = (
    "bash",
    "blacklist",
    "cancel",
    "eval",
    "exec",
    "log",
    "raise",
    "sql",
    "sh",
    "ssh",
    "state",
    "status",
    "task",
    "tasks",
    "thread",
    "threads",
    "trace",
)


if TYPE_CHECKING:
    class Context(commands.Context):
        bot: haruka.Haruka


class CustomHelpCommand(commands.MinimalHelpCommand):
    def __init__(self) -> None:
        command_attrs = {
            "name": "help",
            "description": "Get all available commands or for a specific command.",
            "usage": "help\nhelp <command>",
            "cooldown": commands.CooldownMapping(
                commands.Cooldown(1, 3),
                commands.BucketType.user,
            ),
        }
        super().__init__(command_attrs=command_attrs)

    async def send_bot_help(self, mapping: Mapping[Optional[commands.Cog], List[commands.Command]]) -> None:
        # Initialize
        pref = await prefix(bot, self.context.message)
        embeds = []

        embed = discord.Embed()
        embed.add_field(
            name="💬 General",
            value="```\nabout, avatar, emoji, help, info, ping, prefix, remind, say, source, svinfo\n```",
            inline=False,
        )
        embed.add_field(
            name="✨ Fun",
            value="```\n8ball, card, fact, quote, rickroll, roll\n```",
            inline=False
        )
        embed.add_field(
            name="🔍 Searching",
            value="```\nanime, manga, nhentai, sauce, urban, youtube\n```",
        )
        embeds.append(embed)

        embed = discord.Embed()
        embed.add_field(
            name="🖼️ Images",
            value="```\ndanbooru, nsfw, pixiv, sfw, tenor, zerochan\n```",
            inline=False,
        )
        embed.add_field(
            name="🎶 Music",
            value="```\nadd, export, import, pause, play, playlist, queue, remove, repeat, resume, shuffle, skip, stop, stopafter, vping\n```",
            inline=False,
        )
        embed.add_field(
            name="🛡️ Moderation",
            value="```\nban, kick, mute, unmute\n```",
            inline=False,
        )
        embeds.append(embed)

        for index, embed in enumerate(embeds):
            embed.description = f"You can also invoke command with <@!{bot.user.id}> as a prefix.\nTo get help for a command, type `{pref}help <command>`."
            embed.set_author(
                name=f"{bot.user} Command List",
                icon_url=bot.user.avatar.url,
            )
            embed.set_thumbnail(url=self.context.author.avatar.url if self.context.author.avatar else discord.Embed.Empty)
            embed.set_footer(text=f"Current prefix: {pref} | Page {index + 1}/{len(embeds)}")

        display = emoji_ui.Pagination(embeds)
        await display.send(self.context)

    async def send_command_help(self, command: commands.Command) -> None:
        # Fetch server's prefix
        pref = await prefix(bot, self.context.message)

        if command.aliases and command.qualified_name not in command.aliases:
            command.aliases.insert(0, command.qualified_name)
        elif not command.aliases:
            command.aliases = [command.qualified_name]

        command.usage = command.usage if command.usage else command.qualified_name
        usage = command.usage.replace("\n", f"\n{pref}")

        description = command.description.format(prefix=pref)

        cooldown = command._buckets
        cooldown_notify = "**Cooldown**\nNo cooldown"

        if cooldown._cooldown:
            _cd_time = cooldown._cooldown.per
            cooldown_notify = f"**Cooldown**\n{utils.format(_cd_time)} per {cooldown._type.name}"

        if command.name == "sfw":
            description += ", ".join(f"`{key}`" for key in self.sfw_keys)

        elif command.name == "nsfw":
            description += ", ".join(f"`{key}`" for key in self.nsfw_keys)

        embed = discord.Embed(
            title=command.qualified_name,
            description=f"```\n{pref}{usage}\n```\n**Description**\n{description}\n**Aliases**\n" + ", ".join(f"`{alias}`" for alias in command.aliases) + "\n" + cooldown_notify,
        )
        embed.set_author(name=f"{self.context.author.name}, this is an instruction for {command.qualified_name}!", icon_url=self.context.author.avatar.url if self.context.author.avatar else discord.Embed.Empty)
        await self.context.send(embed=embed)

    async def prepare_help_command(self, ctx: Context, command: Optional[str] = None) -> None:
        await ctx.bot.image.wait_until_ready()
        self.sfw_keys = list(ctx.bot.image.sfw.keys())
        self.sfw_keys.sort()

        self.nsfw_keys = list(ctx.bot.image.nsfw.keys())
        self.nsfw_keys.sort()

    async def command_not_found(self, string: str) -> str:
        if len(string) > 20:
            return "There is no such long command."

        word = await utils.fuzzy_match(string, [k for k in bot.all_commands.keys() if k not in IGNORE])
        return f"No command called `{string}` was found. Did you mean `{word}`?"


bot.help_command = CustomHelpCommand()
