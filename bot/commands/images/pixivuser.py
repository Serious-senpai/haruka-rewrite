from __future__ import annotations

import asyncio
from typing import List, Optional, TYPE_CHECKING

import discord
from discord.ext import commands

from _types import Context
from core import bot
from lib import emoji_ui, pixiv, utils
if TYPE_CHECKING:
    import haruka


class _NavigatorPagination(emoji_ui.EmojiUI):

    __slots__ = ("pages",)
    if TYPE_CHECKING:
        pages: utils.AsyncSequence[pixiv.PixivArtwork]

    def __init__(self, bot: haruka.Haruka, pages: utils.AsyncSequence[pixiv.PixivArtwork]) -> None:
        super().__init__(bot, emoji_ui.NAVIGATOR[:])
        self.pages = pages

    async def get_embed(self, index: int) -> discord.Embed:
        artwork = await self.pages.get(index)
        embed = await artwork.create_embed(session=self.bot.session)
        embed.set_footer(text=f"Artwork {index + 1}/{len(self.pages)}")
        return embed

    async def send(self, target: discord.abc.Messageable, *, user_id: Optional[int] = None) -> None:
        self.initialize_user_id(user_id)

        self.message = await target.send(embed=await self.get_embed(0))
        page = 0

        for emoji in self.allowed_emojis:
            await self.message.add_reaction(emoji)

        while True:
            done, _ = await asyncio.wait([
                self.bot.wait_for("raw_reaction_add", check=self.check),
                self.bot.wait_for("raw_reaction_remove", check=self.check),
            ],
                timeout=300.0,
                return_when=asyncio.FIRST_COMPLETED,
            )

            if done:
                payload: discord.RawReactionActionEvent = done.pop().result()
                action = self.allowed_emojis.index(str(payload.emoji))

                if action == 0:
                    if page > 0:
                        page -= 1
                    else:
                        page = len(self.pages) - 1

                elif action == 1:
                    if page == len(self.pages) - 1:
                        page = 0
                    else:
                        page += 1

                else:
                    raise ValueError(f"Unknown action = {action}")

                self.message = await self.message.edit(embed=await self.get_embed(page))
                await asyncio.sleep(1.0)
            else:
                return await self.timeout()


@bot.command(
    name="pixivuser",
    description="Retrieve all artworks from a Pixiv user",
    usage="pixivuser <user URL>",
)
@commands.cooldown(1, 2, commands.BucketType.user)
async def _pixiv_user_cmd(ctx: Context, *, url: str):
    match = pixiv.USER_PATTERN.fullmatch(url)
    if not match:
        raise commands.UserInputError

    results = await pixiv.PixivArtwork.from_user(int(match.group(2)), session=bot.session)
    if not results:
        return await ctx.send("This user has no artwork!")

    display = _NavigatorPagination(bot, results)
    await display.send(ctx.channel)
