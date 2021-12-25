from __future__ import annotations

import asyncio
import functools
import random
import re
from typing import Any, Dict, Generic, List, Literal, Optional, Tuple, Type, TypeVar

import aiohttp
import discord
from discord.ext import commands

import haruka


IT = TypeVar("IT", bound="ImageSource")


class CategoryNotFound(Exception):
    def __init__(self, category: str) -> None:
        self.category = category


class ImageSource:
    """Represents an image source.

    This class is responsible for registering the categories that
    an image source can provide, as well as getting the image URL
    when there is a request.

    Attributes
    -----
    session: :class:`aiohttp.ClientSession`
        The aiohttp session used to interact with the image source.
    client: ``ImageClient``
        The client that manages this image source.
    """

    __slots__ = (
        "session",
        "client",
    )

    def __init__(self, session: aiohttp.ClientSession, client: ImageClient) -> None:
        self.session: aiohttp.ClientSession = session
        self.client: ImageClient = client

    async def _get_all_endpoints(self) -> Tuple[List[str], List[str]]:
        """This function is a coroutine

        Get all endpoints that this image source can provide.

        Subclasses must implement this.

        Returns
        -----
        Tuple[List[``str``], List[``str``]]
            A 2-tuple containing the sfw and nsfw categories that the
            image source can provide. These categories will be passed
            to ``get`` to get the image URL.
        """
        raise NotImplementedError

    async def get(self, category: str, *, mode: Literal["sfw", "nsfw"]) -> Optional[str]:
        """This function is a coroutine

        Get the URL of the requested category and mode.

        Subclasses must implement this.

        Parameters
        -----
        category: ``str``
            The requested category that the image source can provide,
            should be registered with ``_get_all_endpoints`` first.
        mode: Literal["sfw", "nsfw"]
            Whether the image should be sfw or nsfw.

        Returns
        -----
        Optional[``str``]
            The image URL
        """
        raise NotImplementedError

    @property
    def bot(self) -> haruka.Haruka:
        return self.client.bot


class WaifuPics(ImageSource):

    __slots__ = (
        "session",
        "client",
    )
    endpoints_url: str = "https://api.waifu.pics/endpoints"

    async def _get_all_endpoints(self) -> Tuple[List[str], List[str]]:
        data: Dict[str, List[str]] = {
            "sfw": [],
            "nsfw": [],
        }
        async with self.session.get(self.endpoints_url) as response:
            if response.status == 200:
                data = await response.json()

        return data["sfw"], data["nsfw"]

    async def get(self, category: str, *, mode: Literal["sfw", "nsfw"]) -> Optional[str]:
        url: str = f"https://api.waifu.pics/{mode}/{category}"
        async with self.session.get(url) as response:
            if response.status == 200:
                json: Dict[str, str] = await response.json()
                return json["url"]

        return


class WaifuIm(ImageSource):

    __slots__ = (
        "session",
        "client",
    )
    endpoints_url: str = "https://api.waifu.im/endpoints"

    async def _get_all_endpoints(self) -> Tuple[List[str], List[str]]:
        data: Dict[str, List[str]] = {
            "sfw": [],
            "nsfw": [],
        }

        async with self.session.get(self.endpoints_url) as response:
            if response.status == 200:
                data = await response.json()

        return data["sfw"], data["nsfw"]

    async def get(self, category: str, *, mode: Literal["sfw", "nsfw"]) -> Optional[str]:
        url: str = f"https://api.waifu.im/{mode}/{category}"
        async with self.session.get(url) as response:
            if response.status == 200:
                json: Dict[str, Any] = await response.json()
                return json["images"][0]["url"]

        return


class NekosLife(ImageSource):

    __slots__ = (
        "session",
        "client",
    )
    endpoints_url: str = "https://nekos.life/api/v2/endpoints"
    sfw_converter: Dict[str, str] = {
        "neko gif": "ngif",
        "kitsune": "fox_girl",
    }
    nsfw_converter: Dict[str, str] = {
        "ero neko": "eron",
        "neko gif": "nsfw_neko_gif",
        "lewd kitsune": "lewdk",
        "ero kitsune": "erok",
        "lewd holo": "hololewd",
        "ero holo": "holoero",
        "ero feet": "erofeet",
        "ero yuri": "eroyuri",
        "cum": "cum_jpg",
        "pussy": "pussy_jpg",
        "cum gif": "cum",
        "solo gif": "solog",
        "pussy wank gif": "pwankg",
        "pussy gif": "pussy",
        "random": "Random_hentai_gif",
        "feet gif": "feetg",
        "pussy lick gif": "kuni",
    }

    async def _get_all_endpoints(self) -> Tuple[List[str], List[str]]:
        data: Dict[str, List[str]] = {
            "sfw": ["neko", "neko gif", "kitsune", "holo", "pat", "poke", "hug", "cuddle", "kiss", "feed", "tickle", "smug", "baka", "slap"],
            "nsfw": ["lewd", "ero neko", "neko gif", "lewd kitsune", "ero kitsune", "lewd holo", "ero holo", "ero", "feet", "ero feet", "gasm", "solo", "tits", "yuri", "ero yuri", "hentai", "cum", "blowjob", "femdom", "trap", "pussy", "futanari", "cum gif", "solo gif", "spank", "les", "bj", "pussy wank gif", "pussy gif", "random", "feet gif", "pussy lick gif", "classic", "boobs", "anal"],
        }

        async with self.session.get(self.endpoints_url) as response:
            if response.ok:
                json: List[str] = await response.json()
                for endpoint in json:
                    if "/api/v2/img/" in endpoint:
                        categories: List[str] = [category.strip(r"'") for category in re.findall(r"'\w+'", endpoint)]

                        value: str
                        for name in data["sfw"]:
                            value = self.sfw_converter.get(name, name)
                            if value not in categories:
                                self.bot.log(f"Warning in NekosLife: no SFW endpoint called '{value}' (corresponding name '{name}')")

                        for name in data["nsfw"]:
                            value = self.nsfw_converter.get(name, name)
                            if value not in categories:
                                self.bot.log(f"Warning in NekosLife: no NSFW endpoint called '{value}' (corresponding name '{name}')")

                        return data["sfw"], data["nsfw"]

            return [], []

    async def get(self, category: str, *, mode: Literal["sfw", "nsfw"]) -> Optional[str]:
        if mode == "sfw":
            category = self.sfw_converter.get(category, category)
        else:
            category = self.nsfw_converter.get(category, category)

        url: str = f"https://nekos.life/api/v2/img/{category}"
        async with self.session.get(url) as response:
            if response.status == 200:
                json: Dict[str, str] = await response.json()
                return json["url"]

        return


class Asuna(ImageSource):

    __slots__ = (
        "session",
        "client",
    )
    endpoints_url: str = "https://asuna.ga/api"
    converter: Dict[str, str] = {
        "fox": "wholesome_foxes",
    }

    async def _get_all_endpoints(self) -> Tuple[List[str], List[str]]:
        data: Dict[str, List[str]] = {
            "sfw": ["hug", "kiss", "neko", "pat", "slap", "fox"],
            "nsfw": [],
        }

        async with self.session.get(self.endpoints_url) as response:
            if response.ok:
                json: Dict[str, Any] = await response.json()
                endpoints: List[str] = json["allEndpoints"]

                for name in data["sfw"]:
                    value: str = self.converter.get(name, name)
                    if value not in endpoints:
                        self.bot.log(f"Warning in Asuna: no SFW endpoint called '{value}' (corresponding name '{name}')")

                return data["sfw"], data["nsfw"]

            return [], []

    async def get(self, category: str, *, mode: Literal["sfw", "nsfw"]) -> Optional[str]:
        category = self.converter.get(category, category)
        async with self.session.get(f"https://asuna.ga/api/{category}") as response:
            if response.ok:
                json: Dict[str, str] = await response.json()
                return json["url"]

        return


class ImageClient(Generic[IT]):
    """Represents a client that is used to interact with all
    ImageSource objects.

    Attributes
    -----
    bot: :class:`haruka.Haruka`
        The bot associated with this image client.
    session: :class:`aiohttp.ClientSession`
        The :class:`aiohttp.ClientSession` used to interact with
        the ``ImageSource`` that this client contains.
    sfw: Dict[``str``, List[``ImageSource``]]
        A mapping of SFW categories with all ``ImageSource``
        that can listen to it.
    nsfw: Dict[``str``, List[``ImageSource``]]
        A mapping of NSFW categories with all ``ImageSource``
        that can listen to it.
    sources: List[Type[``ImageSource``]]
        All the ``ImageSource`` that this client contains.
    """
    __slots__ = (
        "bot",
        "sfw",
        "nsfw",
        "session",
        "sources",
    )

    def __init__(self, bot: haruka.Haruka, *sources) -> None:
        self.bot: haruka.Haruka = bot
        self.session: aiohttp.ClientSession = bot.session
        self.sources: List[Type[IT]] = sources
        asyncio.create_task(self._load())

    async def _load(self) -> None:
        """This function is a coroutine

        Register all image categories that this client can listen to.
        This method is scheduled right when this class is initialized.
        """
        self.sfw: Dict[str, List[IT]] = {}
        self.nsfw: Dict[str, List[IT]] = {}
        for command in self.bot.walk_commands():
            if command.name.startswith("*"):
                bot.remove_command(command.name)

        await asyncio.gather(*[self._register(source(self.session, self)) for source in self.sources])
        self.bot.log(f"Loaded {len(self.sources)} ImageSource objects, preparing commands...")

        async def _wrapped_callback(category: str, mode: Literal["sfw", "nsfw"], ctx: commands.Context):
            em: discord.Embed = discord.Embed(
                color=0x2ECC71,
            )
            em.set_author(
                name=f"{ctx.author.name}, this is your image!",
                icon_url=ctx.author.avatar.url if ctx.author.avatar else discord.Embed.Empty,
            )
            em.set_image(url=await self.get(category, mode=mode))

            await ctx.send(embed=em)

        command: commands.Command
        for category in self.sfw:
            command = commands.Command(
                functools.partial(_wrapped_callback, category, "sfw"),
                name="*" + category.replace(" ", "_"),
                description=f"Send you a SFW `{category}` image",
                cooldown=commands.CooldownMapping(
                    commands.Cooldown(1, 2),
                    commands.BucketType.user,
                ),
            )
            self.bot.add_command(command)

        for category in self.nsfw:
            command = commands.Command(
                commands.is_nsfw()(functools.partial(_wrapped_callback, category, "nsfw")),
                name="**" + category.replace(" ", "_"),
                description=f"Send you a NSFW `{category}` image",
                cooldown=commands.CooldownMapping(
                    commands.Cooldown(1, 2),
                    commands.BucketType.user,
                ),
            )
            self.bot.add_command(command)

        self.bot.log("Added all image commands")

    async def _register(self, source: IT) -> None:
        """This function is a coroutine

        Register all endpoints that a ``ImageSource`` can listen
        to and add them to the client listener.

        Parameters
        -----
        :source: ``ImageSource``
            The ``ImageSource`` to analyze.
        """
        if not isinstance(source, ImageSource):
            raise TypeError(f"source must be ImageSource, not {source.__class__.__name__}")

        sfw, nsfw = await source._get_all_endpoints()

        for endpoint in sfw:
            if endpoint not in self.sfw:
                self.sfw[endpoint] = [source]
            else:
                self.sfw[endpoint].append(source)

        for endpoint in nsfw:
            if endpoint not in self.nsfw:
                self.nsfw[endpoint] = [source]
            else:
                self.nsfw[endpoint].append(source)

        self.bot.log(f"Loaded {len(sfw)} SFW endpoints and {len(nsfw)} NSFW endpoints from {source.__class__.__name__}")

    async def get(self, category: str, *, mode: Literal["sfw", "nsfw"] = "sfw") -> Optional[str]:
        """This function is a coroutine

        Get a URL from the requested category. If the requested
        category was not registered, this method will raise
        ``CategoryNotFound``.

        Note that although the category was registered, the
        fetching operation may still fall somehow and ``None``
        is returned instead.

        Parameters
        -----
        category: ``str``
            The image category to fetch URL.

        mode: Literal["sfw", "nsfw"]
            Whether the category belongs to the SFW or NSFW
            collections.

        Returns
        -----
        Optional[``str``]
            The image URL.

        Exceptions
        -----
        ``CategoryNotFound``
            The category does not exist in the requested mode
            (SFW or NSFW).
        """
        if category not in self.sfw and mode == "sfw":
            raise CategoryNotFound(category)

        if category not in self.nsfw and mode == "nsfw":
            raise CategoryNotFound(category)

        if mode == "sfw":
            random.shuffle(self.sfw[category])

            for source in self.sfw[category]:
                image_url: Optional[str] = await source.get(category, mode="sfw")
                if image_url:
                    return image_url

        elif mode == "nsfw":
            random.shuffle(self.nsfw[category])

            for source in self.nsfw[category]:
                image_url: Optional[str] = await source.get(category, mode="nsfw")
                if image_url:
                    return image_url
