from __future__ import annotations

import traceback
from typing import Any, Dict, List, Optional,  TYPE_CHECKING

from discord import app_commands

if TYPE_CHECKING:
    from discord.app_commands.commands import CommandCallback, GroupT, P, T

    import haruka
    from _types import Guild, Interaction


class SlashCommandTree(app_commands.CommandTree):

    if TYPE_CHECKING:
        client: haruka.Haruka

    async def interaction_check(self, interaction: Interaction) -> bool:
        bot = self.client

        guild_id = interaction.guild_id
        if guild_id is not None:
            await bot.reset_inactivity_counter(guild_id)

        if not await bot.is_owner(interaction.user):
            name = interaction.command.name
            if name not in bot._slash_command_count:
                bot._slash_command_count[name] = []

            bot._slash_command_count[name].append(interaction)
        else:
            return True

        row = await bot.conn.fetchrow(f"SELECT * FROM blacklist WHERE id = '{interaction.user.id}';")
        if row is not None:
            await interaction.response.send_message("You are currently in the blacklist!", ephemeral=True)
            return False

        return True

    async def sync(self, *, guild: Optional[Guild] = None) -> List[app_commands.AppCommand]:
        self.client.log("Syncing slash commands...")
        commands = await super().sync(guild=guild)
        self.client.log(f"Synced {len(commands)} commands")
        return commands

    async def on_error(self, interaction: Interaction, error: BaseException) -> None:
        bot = self.client
        client = interaction.client

        if isinstance(error, app_commands.CommandInvokeError):
            return await self.on_error(interaction, error.original)
        elif isinstance(error, app_commands.CheckFailure):
            return

        command = interaction.command
        command_display = f"command '{command.name}'" if command is not None else "unknown interaction"

        bot.log(f"Interaction {interaction.id} ({command_display}) in {interaction.channel_id}/{interaction.guild_id} from {interaction.user} ({interaction.user.id}):")
        bot.log("".join(traceback.format_exception(error.__class__, error, error.__traceback__)))
        await bot.report(f"An error has just occured and was handled by `SlashCommandTree.on_error` (from `{client.__class__.__name__}`)", send_state=False)


class SlashCommand(app_commands.Command):

    __slots__ = ("_guild_only",)
    if TYPE_CHECKING:
        _guild_only: bool

    def __init__(
        self,
        *,
        name: str,
        description: str,
        callback: CommandCallback[GroupT, P, T],
        parent: Optional[app_commands.Group] = None,
        guild_ids: Optional[List[int]] = None,
        guild_only: bool = False
    ) -> None:
        self._guild_only = guild_only
        super().__init__(name=name, description=description, callback=callback, parent=parent, guild_ids=guild_ids)

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data["dm_permission"] = not self._guild_only
