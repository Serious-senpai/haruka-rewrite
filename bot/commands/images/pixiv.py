import discord
from discord.ext import commands

from _types import Context
from core import bot
from lib import emoji_ui, pixiv


@bot.command(
    name="pixiv",
    description="Get image(s) from Pixiv from a searching query, a URL or an ID.\nImages from this command may not have the highest quality, use `{prefix}sauce` to grab their original sources.",
    usage="pixiv <query, URL or ID>",
)
@commands.cooldown(1, 2, commands.BucketType.user)
async def _pixiv_cmd(ctx: Context, *, query: str = ""):
    async with ctx.typing():
        try:
            parsed = await pixiv.parse(query, session=bot.session)
        except pixiv.NSFWArtworkDetected as exc:
            parsed = exc.artwork
            if isinstance(ctx.channel, discord.TextChannel) and not ctx.channel.is_nsfw():
                return await ctx.send("🔞 This artwork is NSFW and can only be shown in a NSFW channel!")

        if isinstance(parsed, pixiv.PixivArtwork):
            return await ctx.send(embed=await parsed.create_embed(session=bot.session))

        if not parsed:
            return await ctx.send("No matching result was found.")

        embeds = []
        for index, artwork in enumerate(parsed):
            embed = await artwork.create_embed(session=bot.session)
            embed.set_footer(text=f"Displaying result #{index + 1}")
            embed.set_author(
                name=f"{ctx.author.name} searched for {query}",
                icon_url=ctx.author.avatar.url if ctx.author.avatar else None,
            )
            embeds.append(embed)

    display = emoji_ui.Pagination(bot, embeds)
    await display.send(ctx.channel)
