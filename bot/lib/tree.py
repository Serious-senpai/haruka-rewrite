from __future__ import annotations

import traceback
from typing import Optional, Union, TYPE_CHECKING

from discord import app_commands

if TYPE_CHECKING:
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

    async def sync(self, *, guild: Optional[Guild] = None) -> None:
        self.client.log("Syncing slash commands...")
        commands = await super().sync(guild=guild)
        self.client.log(f"Synced {len(commands)} commands")

    async def on_error(self, interaction: Interaction, command: Optional[Union[app_commands.Command, app_commands.ContextMenu]], error: app_commands.AppCommandError) -> None:
        bot = self.client
        bot.log(f"'{command.name}' in {interaction.channel_id}/{interaction.guild_id} from {interaction.user} ({interaction.user.id}):")
        bot.log("".join(traceback.format_exception(error.__class__, error, error.__traceback__)))
        await bot.report("An error has just occured and was handled by `SlashCommandTree.on_error`", send_state=False)
