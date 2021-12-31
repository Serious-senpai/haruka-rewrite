import json
import random
from typing import Dict, List

import discord

from core import bot


with open("./bot/assets/misc/wordlist.txt", "r", encoding="utf-8") as f:
    wordlist: List[str] = [row.strip("\n") for row in f.readlines()]


def get_word() -> str:
    return random.choice(wordlist)


with open("./bot/assets/misc/fact.txt", "r", encoding="utf-8") as f:
    facts: List[str] = [row.strip("\n") for row in f.readlines()]


def get_fact() -> str:
    return random.choice(facts)


with open("./bot/assets/misc/8ball.txt", "r", encoding="utf-8") as f:
    answers: List[str] = [row.strip("\n") for row in f.readlines()]


def get_8ball() -> str:
    return random.choice(answers)


with open("./bot/assets/misc/quotes.json", "r", encoding="utf-8") as f:
    quotes: List[Dict[str, str]] = json.load(f)


def get_quote() -> discord.Embed:
    quote: Dict[str, str] = random.choice(quotes)
    embed: discord.Embed = discord.Embed(description=quote["quote"])
    embed.set_author(
        name="From " + quote["anime"],
        icon_url=bot.user.avatar.url,
    )
    embed.set_footer(text=quote["character"])
    return embed
