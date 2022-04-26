from __future__ import annotations

import json
import random
from typing import Dict, Optional, Type, TYPE_CHECKING

import discord
from discord.utils import escape_markdown as escape

from lib.utils import fuzzy_match, slice_string


__all__ = ("Quote",)


with open("./bot/assets/misc/quotes.json", "r", encoding="utf-8") as f:
    quotes = json.load(f)
    animes = {k.casefold(): k for k in quotes.keys()}


class Quote:

    __slots__ = ("anime", "character", "quote")
    if TYPE_CHECKING:
        anime: str
        character: str
        quote: str

    def __init__(self, anime: str, data: Dict[str, str]) -> None:
        self.anime = anime
        self.character = data["character"]
        self.quote = data["quote"]

    def create_embed(self, *, icon_url: str) -> discord.Embed:
        embed = discord.Embed(description=slice_string(escape(self.quote), 4000))
        embed.set_author(name=self.anime, icon_url=icon_url)
        embed.set_footer(text=f"From {self.character}")

        return embed

    @classmethod
    async def get(cls: Type[Quote], anime: Optional[str] = None) -> Quote:
        if anime is not None:
            casefolded = await fuzzy_match(anime.casefold(), animes.keys())
            original = animes[casefolded]
        else:
            original = random.choice(list(quotes.keys()))

        return cls(original, random.choice(quotes[original]))
