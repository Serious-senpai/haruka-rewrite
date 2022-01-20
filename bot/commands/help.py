from typing import Dict, List, Mapping, Optional

import discord
from discord.ext import commands

import utils
import emoji_ui
from core import bot, prefix


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

    def template(self, page: int, pref: str) -> discord.Embed:
        embed = discord.Embed(description=f"You can also invoke command with <@!{bot.user.id}> as a prefix.\nTo get help for a command, type `{pref}help <command>`.")
        embed.set_author(
            name=f"{bot.user} Command List",
            icon_url=bot.user.avatar.url,
        )
        embed.set_thumbnail(url=self.context.author.avatar.url if self.context.author.avatar else discord.Embed.Empty)
        embed.set_footer(text=f"Current prefix: {pref} | Page {page}/4")
        return embed

    async def send_bot_help(self, mapping: Mapping[Optional[commands.Cog], List[commands.Command]]) -> None:
        # Initialize
        pref = await prefix(bot, self.context.message)
        help_em = []

        embed = self.template(1, pref)
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
        help_em.append(embed)

        embed = self.template(2, pref)
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
        help_em.append(embed)

        embed = self.template(3, pref)
        embed.add_field(
            name="🖼️ SFW images",
            value=f"Remember to add the prefix `{pref}`! E.g. `{pref}*waifu`\n" + self._sfw_description,
            inline=False,
        )
        help_em.append(embed)

        embed = self.template(4, pref)
        embed.add_field(
            name="🔞 NSFW images",
            value=f"Remember to add the prefix `{pref}`! E.g. `{pref}**waifu`\n" + self._nsfw_description,
            inline=False,
        )
        help_em.append(embed)

        display = emoji_ui.Pagination(help_em)
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

    async def prepare_help_command(self, ctx: commands.Context, command: Optional[str] = None) -> None:
        await ctx.bot.wait_until_ready()
        self.sfw_keys = list(ctx.bot.image.sfw.keys())
        self.sfw_keys.sort()
        self._sfw_description = "```\n" + ", ".join(f"*{s.replace(' ', '_')}" for s in self.sfw_keys) + "\n```"

        self.nsfw_keys = list(ctx.bot.image.nsfw.keys())
        self.nsfw_keys.sort()
        self._nsfw_description = "```\n" + ", ".join(f"**{s.replace(' ', '_')}" for s in self.nsfw_keys) + "\n```"

    async def command_not_found(self, string: str) -> str:
        if len(string) > 20:
            return "There is no such long command."

        word = await utils.fuzzy_match(string, [k for k in bot.all_commands.keys() if k not in IGNORE], pattern=r"\*{0,2}\w+")
        return f"No command called `{string}` was found. Did you mean `{word}`?"


bot.help_command = CustomHelpCommand()
