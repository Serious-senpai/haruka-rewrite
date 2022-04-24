from __future__ import annotations

import asyncio
import sys
from typing import Optional, Union, TYPE_CHECKING

import discord
from discord.ext import commands

if TYPE_CHECKING:
    import haruka
    import side
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


if TYPE_CHECKING:
    ClientT = Union[haruka.Haruka, side.SideClient]


class Context(commands.Context):
    if TYPE_CHECKING:
        guild: Optional[Guild]
        voice_client: Optional[audio.MusicClient]


class Guild(discord.Guild):
    if TYPE_CHECKING:
        voice_client: Optional[audio.MusicClient]


class Interaction(discord.Interaction):
    if TYPE_CHECKING:
        client: ClientT
        guild: Optional[Guild]


class Member(discord.Member):
    if TYPE_CHECKING:
        guild: Guild
