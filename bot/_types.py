from __future__ import annotations

import asyncio
import sys
from typing import Optional, TYPE_CHECKING

import discord
from discord.ext import commands

if TYPE_CHECKING:
    import haruka
    from lib import audio


if sys.platform == "win32":
    Loop = asyncio.ProactorEventLoop
else:
    try:
        import uvloop
    except ImportError:
        Loop = asyncio.SelectorEventLoop
    else:
        Loop = uvloop.Loop


class Context(commands.Context):
    if TYPE_CHECKING:
        bot: haruka.Haruka
        guild: Optional[Guild]
        voice_client: Optional[audio.MusicClient]


class Guild(discord.Guild):
    if TYPE_CHECKING:
        voice_client: Optional[audio.MusicClient]


class Interaction(discord.Interaction):
    if TYPE_CHECKING:
        guild: Optional[Guild]


class Member(discord.Member):
    if TYPE_CHECKING:
        guild: Guild
