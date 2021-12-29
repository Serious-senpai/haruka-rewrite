import discord


def user_converter(interaction: discord.Interaction, id: str) -> discord.User:
    return discord.User(
        state=interaction._state,
        data=interaction.data["resolved"]["users"][id],
    )


def role_converter(interaction: discord.Interaction, id: str) -> discord.Role:
    return discord.Role(
        guild=interaction.guild,
        state=interaction._state,
        data=interaction.data["resolved"]["roles"][id],
    )


def channel_converter(interaction: discord.Interaction, id: str) -> discord.abc.GuildChannel:
    return interaction.guild.get_channel(int(id))
