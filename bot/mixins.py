from __future__ import annotations

from typing import Any, Optional, TYPE_CHECKING

import discord
from discord.utils import escape_markdown as escape

if TYPE_CHECKING:
    from ._types import ClientT


class ClientMixin:
    def log(self: ClientT, content: Any) -> None:
        prefix = f"{self.__class__.__name__}: "
        logfile = self.logfile
        content = str(content).replace("\n", f"\n{prefix}")
        logfile.write(f"{prefix}{content}\n")
        logfile.flush()

    async def report(
        self: ClientT,
        message: str,
        *,
        send_state: bool = True,
        send_log: bool = True,
    ) -> Optional[discord.Message]:
        if self.owner is not None:
            return await self.owner.send(
                message,
                embed=self.display_status if send_state else None,  # type: ignore
                file=discord.File("./bot/assets/server/log.txt") if send_log else None,  # type: ignore
            )

    @property
    def display_status(self: ClientT) -> discord.Embed:
        guilds = self.guilds
        users = self.users
        emojis = self.emojis
        stickers = self.stickers
        voice_clients = self.voice_clients
        private_channels = self.private_channels
        messages = self._connection._messages

        desc = "**Commands usage:** " + escape(", ".join(f"{command}: {len(uses)}" for command, uses in self._command_count.items())) + "\n**Slash commands usage:** " + escape(", ".join(f"{command}: {len(uses)}" for command, uses in self._slash_command_count.items()))

        embed = discord.Embed(description=desc)
        embed.set_thumbnail(url=self.user.avatar.url)
        embed.set_author(
            name="Internal status",
            icon_url=self.user.avatar.url,
        )

        embed.add_field(
            name="Cached servers",
            value=f"{len(guilds)} servers",
            inline=False,
        )
        embed.add_field(
            name="Cached users",
            value=f"{len(users)} users",
        )
        embed.add_field(
            name="Cached emojis",
            value=f"{len(emojis)} emojis",
        )
        embed.add_field(
            name="Cached stickers",
            value=f"{len(stickers)} stickers",
        )
        embed.add_field(
            name="Cached voice clients",
            value=f"{len(voice_clients)} voice clients",
        )
        embed.add_field(
            name="Cached DM channels",
            value=f"{len(private_channels)} channels",
        )
        embed.add_field(
            name="Cached messages",
            value=f"{len(messages)} messages",
            inline=False,
        )
        embed.add_field(
            name="Uptime",
            value=discord.utils.utcnow() - self.uptime,
            inline=False,
        )

        return embed
