import discord
from discord.utils import escape_markdown as escape


def user_info(user: discord.User) -> discord.Embed:
    name: str = escape(user.name)
    display: str = escape(str(user))
    info_em: discord.Embed = discord.Embed(
        title=f"{display} Information",
        description=f"**Name** {name}\n**Created** {(discord.utils.utcnow() - user.created_at).days} days ago\n**ID** {user.id}",
        color=0x2ECC71,
        timestamp=discord.utils.utcnow(),
    )
    info_em.set_thumbnail(url=user.avatar.url if user.avatar else discord.Embed.Empty)
    info_em.set_image(url=user.banner.url if user.banner else discord.Embed.Empty)
    info_em.set_footer(text="From Discord")
    return info_em


def server_info(guild: discord.Guild) -> discord.Embed:
    name: str = escape(guild.name)
    sv_em: discord.Embed = discord.Embed(
        title="Server info",
        description=f"**Server name** {name}\n**Server ID** {guild.id}\n**Member count** {guild.member_count}",
        color=0x2ECC71,
    )
    sv_em.add_field(
        name="Created",
        value=f"{(discord.utils.utcnow() - guild.created_at).days} days ago"
    )
    sv_em.add_field(
        name="Text channels",
        value=len(guild.text_channels)
    )
    sv_em.add_field(
        name="Voice channels",
        value=len(guild.voice_channels)
    )
    sv_em.add_field(
        name="Emojis",
        value=len(guild.emojis)
    )
    sv_em.set_thumbnail(url=guild.icon.url if guild.icon else discord.Embed.Empty)
    sv_em.set_image(url=guild.banner.url if guild.banner else discord.Embed.Empty)
    return sv_em
