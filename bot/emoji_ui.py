from __future__ import annotations

import asyncio
import contextlib
import random
from typing import Optional, List, Set, Tuple, Type, TypeVar, Union, TYPE_CHECKING

import discord

from core import bot


ET = TypeVar("ET", bound="EmojiUI")


# Frequently used emoji lists
CHECKER = ("❌", "✔️")
CHOICES = ("1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣")
NAVIGATOR = ("⬅️", "➡️")


class EmojiUI:
    """Base class for emoji-based UIs."""

    __slots__ = ("message", "user_id", "allowed_emojis")
    if TYPE_CHECKING:
        message: Optional[discord.Message]
        user_id: Optional[int]
        allowed_emojis: Tuple[str, ...]

    def check(self, payload: discord.RawReactionActionEvent) -> bool:
        if self.user_id is not None:
            return self.message.id == payload.message_id and payload.user_id == self.user_id and str(payload.emoji) in self.allowed_emojis
        else:
            return self.message.id == payload.message_id and not payload.user_id == bot.user.id and str(payload.emoji) in self.allowed_emojis

    async def timeout(self, pending: Optional[Set[Union[asyncio.Future, asyncio.Task]]] = None) -> None:
        """This function is a coroutine

        This is called when the interaction times out to ensure
        proper cleanup.
        """
        if pending:
            for task in pending:
                if not task.done():
                    task.cancel()

        with contextlib.suppress(discord.HTTPException):
            await self.message.edit("This message has timed out.")
            await self.message.clear_reactions()


class Pagination(EmojiUI):
    """Represents a message manager with pagination
    utilities powered by emojis.

    The maximum number of pages is 6.

    Attributes
    -----
    pages: List[``discord.Embed``]
        A list of pages as embeds

    message: Optional[``discord.Message``]
        The message used to interact.
    """

    __slots__ = ("pages",)
    if TYPE_CHECKING:
        pages: List[discord.Embed]

    def __init__(self, pages: List[discord.Embed]) -> None:
        self.pages = pages

        if len(self.pages) > 6:
            raise ValueError("Number of pages exceeded the limit of 6.")

        self.message = None
        self.allowed_emojis = CHOICES[:len(self.pages)]

    async def send(self, target: discord.abc.Messageable, *, user_id: Optional[int] = None) -> None:
        """This function is a coroutine

        Send message to ``target`` and interact with the user until
        it times out.

        Parameters
        -----
        target: ``discord.abc.Messageable``
            The target to interact with.

        user_id: Optional[``int``]
            The user ID to interact specifically. If this is set to
            ``None``, anyone can interact with this message except
            this bot itself.
        """
        self.message = await target.send(embed=self.pages[0])
        self.user_id = user_id

        for emoji in self.allowed_emojis:
            await self.message.add_reaction(emoji)

        while True:
            done, pending = await asyncio.wait([
                bot.wait_for("raw_reaction_add", check=self.check),
                bot.wait_for("raw_reaction_remove", check=self.check),
            ],
                timeout=300.0,
                return_when=asyncio.FIRST_COMPLETED,
            )

            if done:
                payload = done.pop().result()
                page = self.allowed_emojis.index(str(payload.emoji))
                await self.message.edit(embed=self.pages[page])
                await asyncio.sleep(1.0)
            else:
                return await self.timeout(pending)


class RandomPagination(EmojiUI):
    """Represents a message manager with random
    pagination utilities powered by emojis.

    Attributes
    -----
    pages: List[``discord.Embed``]
        A list of pages as embeds

    message: Optional[``discord.Message``]
        The message used to interact.
    """

    __slots__ = ("pages",)
    if TYPE_CHECKING:
        pages: List[discord.Embed]

    def __init__(self, pages: List[discord.Embed]) -> None:
        self.pages = pages
        self.message = None
        self.allowed_emojis = ("🔄",)

    async def send(self, target: discord.abc.Messageable, *, user_id: Optional[int] = None) -> None:
        """This function is a coroutine

        Send message to ``target`` and interact with the user until
        it times out.

        Parameters
        -----
        target: ``discord.abc.Messageable``
            The target to interact with.

        user_id: Optional[``int``]
            The user ID to interact specifically. If this is set to
            ``None``, anyone can interact with this message except
            this bot itself.
        """
        self.user_id = user_id

        while True:
            if self.message:
                try:
                    await self.message.edit(embed=random.choice(self.pages))
                    await asyncio.sleep(1.0)
                except discord.HTTPException:
                    self.message = None

            if not self.message:
                self.message = await target.send(embed=random.choice(self.pages))
                await self.message.add_reaction("🔄")

            done, pending = await asyncio.wait([
                bot.wait_for("raw_reaction_add", check=self.check),
                bot.wait_for("raw_reaction_remove", check=self.check),
            ],
                timeout=300.0,
                return_when=asyncio.FIRST_COMPLETED,
            )

            if not done:
                return await self.timeout(pending)


class NavigatorPagination(EmojiUI):
    """Represents a message manager with navigator pagination
    utilities powered by emojis.

    This pagination is not limited in the number of pages.

    Attributes
    -----
    pages: List[``discord.Embed``]
        A list of pages as embeds

    message: Optional[``discord.Message``]
        The message used to interact.
    """

    __slots__ = ("pages",)
    if TYPE_CHECKING:
        pages: List[discord.Embed]

    def __init__(self, pages: List[discord.Embed]) -> None:
        self.pages = pages
        self.message = None
        self.allowed_emojis = NAVIGATOR[:]

    async def send(self, target: discord.abc.Messageable, *, user_id: Optional[int] = None) -> None:
        """This function is a coroutine

        Send message to ``target`` and interact with the user until
        it times out.

        Parameters
        -----
        target: ``discord.abc.Messageable``
            The target to interact with.

        user_id: Optional[``int``]
            The user ID to interact specifically. If this is set to
            ``None``, anyone can interact with this message except
            this bot itself.
        """
        self.message = await target.send(embed=self.pages[0])
        self.user_id = user_id
        page = 0

        for emoji in self.allowed_emojis:
            await self.message.add_reaction(emoji)

        while True:
            done, pending = await asyncio.wait([
                bot.wait_for("raw_reaction_add", check=self.check),
                bot.wait_for("raw_reaction_remove", check=self.check),
            ],
                timeout=300.0,
                return_when=asyncio.FIRST_COMPLETED,
            )

            if done:
                payload = done.pop().result()
                action = self.allowed_emojis.index(str(payload.emoji))

                if action == 0:
                    if page > 0:
                        page -= 1
                    else:
                        page = len(self.pages) - 1

                else:  # action == 1
                    if page == len(self.pages) - 1:
                        page = 0
                    else:
                        page += 1

                await self.message.edit(embed=self.pages[page])
                await asyncio.sleep(1.0)
            else:
                return await self.timeout(pending)


class SelectMenu(EmojiUI):
    """Represents a select menu powered by emojis

    The maximum number of options is 6.

    Attributes
    -----
    message: ``discord.Message``
        The message used to interact.

    nargs: ``int``
        The number of options.
    """

    __slots__ = ("nargs",)
    if TYPE_CHECKING:
        nargs: int
        message: discord.Message

    def __init__(self, message: discord.Message, nargs: int) -> None:
        self.nargs = nargs

        if self.nargs > 6:
            raise ValueError("Number of options exceeded the limit of 6")

        self.message = message
        self.allowed_emojis = CHOICES[:self.nargs]

    async def listen(self, user_id: int) -> Optional[int]:
        """This function is a coroutine

        Add reactions to the message and start listening to the
        user.

        Parameters
        -----
        user_id: ``int``
            The user ID to listen to.

        Returns
        -----
        Optional[``int``]
            The index of the selected option, starting from 0,
            or ``None`` if the menu times out.
        """
        self.user_id = user_id

        for emoji in self.allowed_emojis:
            await self.message.add_reaction(emoji)

        try:
            payload = await bot.wait_for("raw_reaction_add", check=self.check, timeout=300.0)
        except asyncio.TimeoutError:
            await self.timeout()
            return
        else:
            with contextlib.suppress(discord.HTTPException):
                await self.message.delete()

            choice = self.allowed_emojis.index(str(payload.emoji))
            return choice


class YesNoSelection(EmojiUI):

    __slots__ = ()

    def __init__(self, message: discord.Message) -> None:
        self.message = message
        self.allowed_emojis = CHECKER

    async def listen(self, user_id: Optional[int] = None) -> Optional[bool]:
        self.user_id = user_id
        for emoji in self.allowed_emojis:
            await self.message.add_reaction(emoji)

        try:
            payload = await bot.wait_for("raw_reaction_add", check=self.check, timeout=300.0)
        except asyncio.TimeoutError:
            await self.timeout()
            return
        else:
            with contextlib.suppress(discord.HTTPException):
                await self.message.delete()

            choice = self.allowed_emojis.index(str(payload.emoji))
            return choice == 1
