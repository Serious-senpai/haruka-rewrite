from __future__ import annotations

import traceback
from typing import List, Optional, TypeVar, TYPE_CHECKING

from discord import app_commands

if TYPE_CHECKING:
    import haruka
    import side
    from _types import ClientT, Guild, Interaction

    TreeT = TypeVar("TreeT", app_commands.CommandTree[ClientT])


class TreeMixin:
    async def sync(self: TreeT, *, guild: Optional[Guild] = None) -> List[app_commands.AppCommand]:
        client = self.client
        client.log("Syncing slash commands...")
        commands = await super().sync(guild=guild)
        client.log(f"Synced {len(commands)} commands")
        return commands

    async def on_error(self: TreeT, interaction: Interaction, error: BaseException) -> None:
        client = self.client

        if isinstance(error, app_commands.CommandInvokeError):
            return await self.on_error(interaction, error.original)
        elif isinstance(error, app_commands.CheckFailure):
            return

        command = interaction.command
        command_display = f"command '{command.name}'" if command is not None else "unknown interaction"

        client.log(f"Interaction {interaction.id} ({command_display}) in {interaction.channel_id}/{interaction.guild_id} from {interaction.user} ({interaction.user.id}):")
        client.log("".join(traceback.format_exception(error.__class__, error, error.__traceback__)))
        await client.report(f"An error has just occured and was handled by `SlashCommandTree.on_error` (from `{client.__class__.__name__}`)", send_state=False)


class SlashCommandTree(TreeMixin, app_commands.CommandTree):

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


class SideClientTree(TreeMixin, app_commands.CommandTree):

    if TYPE_CHECKING:
        client: side.SideClient

    async def interaction_check(self, interaction: Interaction) -> bool:
        bot = self.client

        if interaction.user != bot.owner:
            name = interaction.command.name
            if name not in bot._slash_command_count:
                bot._slash_command_count[name] = []

            bot._slash_command_count[name].append(interaction)

        return True
