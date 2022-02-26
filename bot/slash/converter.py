from typing import Literal

import discord

from _types import Interaction


def subcommand_converter(interaction: Interaction, **options) -> Literal[True]:
    return True


def user_converter(interaction: Interaction, **options) -> discord.User:
    id = options["value"]
    return discord.User(
        state=interaction._state,
        data=interaction.data["resolved"]["users"][id],
    )


def role_converter(interaction: Interaction, **options) -> discord.Role:
    id = options["value"]
    return discord.Role(
        guild=interaction.guild,
        state=interaction._state,
        data=interaction.data["resolved"]["roles"][id],
    )


def channel_converter(interaction: Interaction, **options) -> discord.abc.GuildChannel:
    id = options["value"]
    return interaction.guild.get_channel(int(id))
