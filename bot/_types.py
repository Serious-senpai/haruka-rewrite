from __future__ import annotations

from typing import Optional, TYPE_CHECKING

import discord
from discord.ext import commands

if TYPE_CHECKING:
    from lib import audio


class Context(commands.Context):
    @property
    def guild(self) -> Optional[Guild]:
        return super().guild

    @property
    def voice_client(self) -> Optional[audio.MusicClient]:
        return super().voice_client


class Guild(discord.Guild):
    @property
    def voice_client(self) -> Optional[audio.MusicClient]:
        return super().voice_client


class Interaction(discord.Interaction):
    @property
    def guild(self) -> Optional[Guild]:
        return super().guild


class Member(discord.Member):
    if TYPE_CHECKING:
        guild: Guild
