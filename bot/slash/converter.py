from typing import Literal

import discord


def subcommand_converter(interaction: discord.Interaction, **option) -> Literal[True]:
    return True


def user_converter(interaction: discord.Interaction, **option) -> discord.User:
    id = option["value"]
    return discord.User(
        state=interaction._state,
        data=interaction.data["resolved"]["users"][id],
    )


def role_converter(interaction: discord.Interaction, **option) -> discord.Role:
    id = option["value"]
    return discord.Role(
        guild=interaction.guild,
        state=interaction._state,
        data=interaction.data["resolved"]["roles"][id],
    )


def channel_converter(interaction: discord.Interaction, **option) -> discord.abc.GuildChannel:
    id = option["value"]
    return interaction.guild.get_channel(int(id))
