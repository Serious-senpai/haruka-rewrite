import json
import random
from typing import Dict, List, Optional

import discord
from discord.utils import escape_markdown as escape

import utils
from core import bot


with open("./bot/assets/misc/fact.txt", "r", encoding="utf-8") as f:
    facts: List[str] = [row.strip("\n") for row in f.readlines()]


def get_fact() -> str:
    return random.choice(facts)


with open("./bot/assets/misc/8ball.txt", "r", encoding="utf-8") as f:
    answers: List[str] = [row.strip("\n") for row in f.readlines()]


def get_8ball() -> str:
    return random.choice(answers)


with open("./bot/assets/misc/quotes.json", "r", encoding="utf-8") as f:
    quotes: Dict[str, List[Dict[str, str]]] = json.load(f)
    quotes_k: Dict[str, str] = dict((k.casefold(), k) for k in quotes.keys())


async def get_quote(anime: Optional[str] = None) -> discord.Embed:
    original_name: Optional[str]
    if anime is not None:
        anime = anime.casefold()
        original_name = quotes_k.get(anime)
        if original_name is None:
            original_name = await utils.fuzzy_match(anime, quotes_k.keys())
    else:
        original_name = random.choice(list(quotes_k.values()))

    element: Dict[str, str]= random.choice(quotes[original_name])
    embed: discord.Embed = discord.Embed(description=escape(element["quote"]))
    embed.set_author(
        name="From " + original_name,
        icon_url=bot.user.avatar.url,
    )
    embed.set_footer(text=element["character"])
    return embed
