import discord


def UserConverter(interaction: discord.Interaction, id: str) -> discord.User:
    return discord.User(
        state=interaction._state,
        data=interaction.data["resolved"]["users"][id],
    )


def RoleConverter(interaction: discord.Interaction, id: str) -> discord.Role:
    return discord.Role(
        guild=interaction.guild,
        state=interaction._state,
        data=interaction.data["resolved"]["roles"][id],
    )


def ChannelConverter(interaction: discord.Interaction, id: str) -> discord.abc.GuildChannel:
    return interaction.guild.get_channel(int(id))
