import discord
from discord.utils import escape_markdown as escape


def user_info(user: discord.User) -> discord.Embed:
    embed = discord.Embed(description=f"**Name** {escape(user.name)}\n**Created** {(discord.utils.utcnow() - user.created_at).days} days ago\n**ID** {user.id}")
    embed.set_author(
        name=f"{user} Information",
        icon_url=user.avatar.url if user.avatar else None,
    )
    embed.set_thumbnail(url=user.avatar.url if user.avatar else None)
    embed.set_image(url=user.banner.url if user.banner else None)
    embed.set_footer(text="From Discord")
    return embed


def server_info(guild: discord.Guild) -> discord.Embed:
    embed = discord.Embed(description=f"**Server name** {escape(guild.name)}\n**Server ID** {guild.id}\n**Member count** {guild.member_count}")
    embed.add_field(
        name="Created",
        value=f"{(discord.utils.utcnow() - guild.created_at).days} days ago"
    )
    embed.add_field(
        name="Text channels",
        value=len(guild.text_channels)
    )
    embed.add_field(
        name="Voice channels",
        value=len(guild.voice_channels)
    )
    embed.add_field(
        name="Emojis",
        value=len(guild.emojis)
    )
    embed.set_author(
        name="Server Information",
        icon_url=guild.icon.url if guild.icon else None,
    )
    embed.set_thumbnail(url=guild.icon.url if guild.icon else None)
    embed.set_image(url=guild.banner.url if guild.banner else None)
    return embed
