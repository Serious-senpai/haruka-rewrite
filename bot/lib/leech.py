import json
import random
from typing import Optional

import discord
from discord.utils import escape_markdown as escape

from .utils import fuzzy_match


with open("./bot/assets/misc/fact.txt", "r", encoding="utf-8") as f:
    facts = [row.strip("\n") for row in f.readlines()]


def get_fact() -> str:
    return random.choice(facts)


with open("./bot/assets/misc/8ball.txt", "r", encoding="utf-8") as f:
    answers = [row.strip("\n") for row in f.readlines()]


def get_8ball() -> str:
    return random.choice(answers)


with open("./bot/assets/misc/quotes.json", "r", encoding="utf-8") as f:
    quotes = json.load(f)
    quotes_k = dict((k.casefold(), k) for k in quotes.keys())


async def get_quote(anime: Optional[str] = None, *, icon_url: Optional[str] = None) -> discord.Embed:
    if anime is not None:
        anime = anime.casefold()
        original_name = quotes_k.get(anime)
        if original_name is None:
            anime = await fuzzy_match(anime, quotes_k.keys())
            original_name = quotes_k[anime]
    else:
        original_name = random.choice(list(quotes_k.values()))

    element = random.choice(quotes[original_name])
    embed = discord.Embed(description=escape(element["quote"]))
    embed.set_footer(text=element["character"])

    if icon_url:
        embed.set_author(
            name="From " + original_name,
            icon_url=icon_url,
        )

    return embed
