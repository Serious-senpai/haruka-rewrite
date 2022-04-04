from __future__ import annotations

import asyncio
import contextlib
import random
from typing import Optional, List, Set, Tuple, TypeVar, Union, TYPE_CHECKING

import discord

if TYPE_CHECKING:
    import haruka


ET = TypeVar("ET", bound="EmojiUI")


# Frequently used emoji lists
CHECKER = ("❌", "✔️")
CHOICES = ("1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣")
NAVIGATOR = ("⬅️", "➡️")


def cancel_tasks(tasks: Set[Union[asyncio.Future, asyncio.Task]]) -> None:
    for task in tasks:
        if not task.done():
            task.cancel()


class EmojiUI:
    """Base class for emoji-based UIs."""

    __slots__ = ("bot", "message", "allowed_emojis", "__user_id")
    if TYPE_CHECKING:
        bot: haruka.Haruka
        message: Optional[discord.Message]
        allowed_emojis: Tuple[str, ...]
        __user_id: Optional[int]

    def __init__(self, bot: haruka.Haruka, allowed_emojis: Tuple[str, ...]) -> None:
        self.bot = bot
        self.allowed_emojis = allowed_emojis

        self.message = None
        self.__user_id = None

    @property
    def user_id(self) -> Optional[int]:
        return self.__user_id

    @user_id.setter
    def user_id(self, value: int) -> None:
        try:
            self.__user_id = int(value)
        except TypeError as exc:
            raise ValueError(f"Cannot cannot convert {repr(value)} to int") from exc

    def check(self, payload: discord.RawReactionActionEvent) -> bool:
        if self.user_id is not None:
            return payload.message_id == self.message.id and str(payload.emoji) in self.allowed_emojis and payload.user_id == self.user_id
        else:
            return payload.message_id == self.message.id and str(payload.emoji) in self.allowed_emojis and not payload.user_id == self.bot.user.id

    async def timeout(self) -> None:
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

    def __init__(self, bot: haruka.Haruka, pages: List[discord.Embed]) -> None:
        self.pages = pages
        super().__init__(bot, CHOICES[:len(self.pages)])

        if len(self.pages) > 6:
            raise ValueError("Number of pages exceeded the limit of 6.")

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
            the bot itself.
        """
        self.message = await target.send(embed=self.pages[0])
        self.user_id = user_id

        for emoji in self.allowed_emojis:
            await self.message.add_reaction(emoji)

        while True:
            done, pending = await asyncio.wait([
                self.bot.wait_for("raw_reaction_add", check=self.check),
                self.bot.wait_for("raw_reaction_remove", check=self.check),
            ],
                timeout=300.0,
                return_when=asyncio.FIRST_COMPLETED,
            )

            if done:
                payload: discord.RawReactionActionEvent = done.pop().result()
                page = self.allowed_emojis.index(str(payload.emoji))
                await self.message.edit(embed=self.pages[page])
                await asyncio.sleep(1.0)
            else:
                cancel_tasks(pending)
                return await self.timeout()


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

    def __init__(self, bot: haruka.Haruka, pages: List[discord.Embed]) -> None:
        super().__init__(bot, ("🔄",))
        self.pages = pages

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
            the bot itself.
        """
        if user_id is not None:
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
                self.bot.wait_for("raw_reaction_add", check=self.check),
                self.bot.wait_for("raw_reaction_remove", check=self.check),
            ],
                timeout=300.0,
                return_when=asyncio.FIRST_COMPLETED,
            )

            if not done:
                cancel_tasks(pending)
                return await self.timeout()


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

    def __init__(self, bot: haruka.Haruka, pages: List[discord.Embed]) -> None:
        super().__init__(bot, NAVIGATOR[:])
        self.pages = pages

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
            the bot itself.
        """
        if user_id is not None:
            self.user_id = user_id

        self.message = await target.send(embed=self.pages[0])
        page = 0

        for emoji in self.allowed_emojis:
            await self.message.add_reaction(emoji)

        while True:
            done, pending = await asyncio.wait([
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

                else:  # action == 1
                    if page == len(self.pages) - 1:
                        page = 0
                    else:
                        page += 1

                await self.message.edit(embed=self.pages[page])
                await asyncio.sleep(1.0)
            else:
                cancel_tasks(pending)
                return await self.timeout()


class SelectMenu(EmojiUI):
    """Represents a select menu powered by emojis

    The maximum number of options is 6.

    Attributes
    -----
    message: ``discord.Message``
        The message used to interact.

    args_count: ``int``
        The number of options.
    """

    __slots__ = ("args_count",)
    if TYPE_CHECKING:
        args_count: int

    def __init__(self, bot: haruka.Haruka, message: discord.Message, args_count: int) -> None:
        self.args_count = args_count

        if self.args_count > 6:
            raise ValueError("Number of options exceeded the limit of 6")

        super().__init__(bot, CHOICES[:self.args_count])
        self.message = message

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
            payload: discord.RawReactionActionEvent = await self.bot.wait_for("raw_reaction_add", check=self.check, timeout=300.0)
        except asyncio.TimeoutError:
            return await self.timeout()
        else:
            with contextlib.suppress(discord.HTTPException):
                await self.message.delete()

            choice = self.allowed_emojis.index(str(payload.emoji))
            return choice


class YesNoSelection(EmojiUI):

    __slots__ = ()

    def __init__(self, bot: haruka.Haruka, message: discord.Message) -> None:
        super().__init__(bot, CHECKER[:])
        self.message = message

    async def listen(self, user_id: Optional[int] = None) -> Optional[bool]:
        if user_id is not None:
            self.user_id = user_id

        for emoji in self.allowed_emojis:
            await self.message.add_reaction(emoji)

        try:
            payload: discord.RawReactionActionEvent = await self.bot.wait_for("raw_reaction_add", check=self.check, timeout=300.0)
        except asyncio.TimeoutError:
            return await self.timeout()
        else:
            with contextlib.suppress(discord.HTTPException):
                await self.message.delete()

            choice = self.allowed_emojis.index(str(payload.emoji))
            return choice == 1
