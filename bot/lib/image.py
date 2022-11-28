from __future__ import annotations

import asyncio
import contextlib
import random
import re
from typing import (
    ClassVar,
    Dict,
    Generic,
    List,
    Literal,
    Optional,
    Set,
    Tuple,
    Type,
    Union,
    TYPE_CHECKING,
)

import aiohttp
import yarl

if TYPE_CHECKING:
    import haruka


class CategoryNotFound(Exception):

    __slots__ = ("category",)

    def __init__(self, category: str) -> None:
        self.category = category


class ImageSource:
    """Represents an image source.

    This class is responsible for registering the categories that
    an image source can provide, as well as getting the image URL
    when there is a request.

    Attributes
    -----
    session: ``aiohttp.ClientSession``
        The aiohttp session used to interact with the image source.
    client: ``ImageClient``
        The client that manages this image source.
    """

    __slots__ = ("session", "client")
    if TYPE_CHECKING:
        session: aiohttp.ClientSession
        client: ImageClient

    def __init__(self, session: aiohttp.ClientSession, client: ImageClient) -> None:
        self.session = session
        self.client = client

    async def _get_all_endpoints(self) -> Tuple[Set[str], Set[str]]:
        """This function is a coroutine

        Get all endpoints that this image source can provide.

        Subclasses must implement this.

        Returns
        -----
        Tuple[Set[``str``], Set[``str``]]
            A 2-tuple containing the sfw and nsfw categories that the
            image source can provide. These categories will be passed
            to ``get`` to get the image URL.
        """
        raise NotImplementedError

    async def get(self, category: str, *, mode: Literal["sfw", "nsfw"] = "sfw") -> Optional[str]:
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

    def get_url(self, category: str, *, mode: Literal["sfw", "nsfw"] = "sfw") -> Union[str, yarl.URL]:
        """Get the API URL for the specified category and mode.

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
        Union[``str``, ``yarl.URL``]
            The API URL
        """
        raise NotImplementedError

    def __str__(self) -> str:
        raise NotImplementedError


class WaifuPics(ImageSource):

    __slots__ = ("session", "client")
    endpoints_url: ClassVar[str] = "https://api.waifu.pics/endpoints"

    async def _get_all_endpoints(self) -> Tuple[Set[str], Set[str]]:
        sfw = set()
        nsfw = set()

        try:
            async with self.session.get(self.endpoints_url) as response:
                if response.status == 200:
                    data = await response.json(encoding="utf-8")
                    sfw |= set(data["sfw"])
                    nsfw |= set(data["nsfw"])
        except (aiohttp.ClientError, asyncio.TimeoutError):
            pass

        return sfw, nsfw

    async def get(self, category: str, *, mode: Literal["sfw", "nsfw"] = "sfw") -> Optional[str]:
        url = self.get_url(category, mode=mode)
        async with self.session.get(url) as response:
            if response.status == 200:
                json = await response.json(encoding="utf-8")
                return json["url"]

    def get_url(self, category: str, *, mode: Literal["sfw", "nsfw"] = "sfw") -> str:
        return f"https://api.waifu.pics/{mode}/{category}"

    def __str__(self) -> str:
        return "waifu.pics"


class WaifuIm(ImageSource):

    __slots__ = ("session", "client")
    endpoints_url: ClassVar[str] = "https://api.waifu.im/tags/?full=true"

    async def _get_all_endpoints(self) -> Tuple[Set[str], Set[str]]:
        sfw = set()
        nsfw = set()

        try:
            async with self.session.get(self.endpoints_url) as response:
                if response.status == 200:
                    data = await response.json(encoding="utf-8")

                    for tag in data["versatile"]:
                        sfw.add(tag["name"])
                        nsfw.add(tag["name"])

                    for tag in data["nsfw"]:
                        nsfw.add(tag["name"])

        except (aiohttp.ClientError, asyncio.TimeoutError):
            pass

        return sfw, nsfw

    async def get(self, category: str, *, mode: Literal["sfw", "nsfw"] = "sfw") -> Optional[str]:
        url = self.get_url(category, mode=mode)
        async with self.session.get(url) as response:
            if response.status == 200:
                json = await response.json(encoding="utf-8")
                return json["images"][0]["url"]

    def get_url(self, category: str, *, mode: Literal["sfw", "nsfw"] = "sfw") -> yarl.URL:
        return yarl.URL.build(
            scheme="https",
            host="api.waifu.im",
            path="/search",
            query={
                "included_tags": category,
                "is_nsfw": str(mode == "nsfw"),
            },
        )

    def __str__(self) -> str:
        return "waifu.im"


class NekosLife(ImageSource):

    __slots__ = ("session", "client")
    endpoints_url: ClassVar[str] = "https://nekos.life/api/v2/endpoints"
    converter: ClassVar[Dict[str, str]] = {
        "neko gif": "ngif",
        "kitsune": "fox_girl",
    }

    async def _get_all_endpoints(self) -> Tuple[Set[str], Set[str]]:
        sfw = set(["neko", "smug", "woof", "avatar", "wallpaper", "cuddle", "slap", "hug", "meow", "kiss", "tickle", "waifu", "lewd"])
        nsfw = set()

        sfw.update(self.converter.keys())
        return sfw, nsfw

    async def get(self, category: str, *, mode: Literal["sfw", "nsfw"] = "sfw") -> Optional[str]:
        url = self.get_url(category, mode=mode)
        async with self.session.get(url) as response:
            if response.status == 200:
                json = await response.json(encoding="utf-8")
                return json["url"]

    def get_url(self, category: str, *, mode: Literal["sfw", "nsfw"] = "sfw") -> str:
        category = self.converter.get(category, category)
        return f"https://nekos.life/api/v2/img/{category}"

    def __str__(self) -> str:
        return "nekos.life"


class Asuna(ImageSource):

    __slots__ = ("session", "client")
    endpoints_url: ClassVar[str] = "https://asuna.ga/api"
    converter: ClassVar[Dict[str, str]] = {
        "fox": "wholesome_foxes",
    }

    async def _get_all_endpoints(self) -> Tuple[Set[str], Set[str]]:
        sfw = set(["hug", "kiss", "neko", "pat", "slap", "fox"])
        nsfw = set()  # type: ignore

        try:
            async with self.session.get(self.endpoints_url) as response:
                if response.ok:
                    json = await response.json(encoding="utf-8")
                    categories = json["allEndpoints"]

                    to_remove = set()
                    for name in sfw:
                        value = self.converter.get(name, name)
                        if value not in categories:
                            to_remove.add(value)

                    sfw -= to_remove

        except (aiohttp.ClientError, asyncio.TimeoutError):
            return set(), set()
        else:
            return sfw, nsfw

    async def get(self, category: str, *, mode: Literal["sfw", "nsfw"] = "sfw") -> Optional[str]:
        url = self.get_url(category, mode=mode)
        async with self.session.get(url) as response:
            if response.ok:
                json = await response.json(encoding="utf-8")
                return json["url"]

    def get_url(self, category: str, *, mode: Literal["sfw", "nsfw"] = "sfw") -> str:
        category = self.converter.get(category, category)
        return f"https://asuna.ga/api/{category}"

    def __str__(self) -> str:
        return "asuna.ga"


class ImageClient:
    """Represents a client that is used to interact with all
    ImageSource objects.

    Attributes
    -----
    session: ``aiohttp.ClientSession``
        The ``aiohttp.ClientSession`` used to interact with
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
        "_ready",
        "bot",
        "log",
        "sfw",
        "nsfw",
        "sources",
    )
    if TYPE_CHECKING:
        _ready: asyncio.Event
        bot: haruka.Haruka
        sources: Tuple[Type[ImageSource]]
        sfw: Dict[str, List[ImageSource]]
        nsfw: Dict[str, List[ImageSource]]

    def __init__(self, bot: haruka.Haruka) -> None:
        self._ready = asyncio.Event()
        self.bot = bot
        self.log = bot.log
        self.sources = (WaifuPics, WaifuIm, NekosLife, Asuna)  # type: ignore

    @property
    def session(self) -> aiohttp.ClientSession:
        return self.bot.session

    async def prepare(self) -> None:
        """This function is a coroutine

        Register all image categories that this client can listen to.

        This method must be called before any other operations.
        """
        self.sfw = {}
        self.nsfw = {}

        with contextlib.suppress(BaseException):
            await asyncio.gather(*[self._register(source(self.session, self)) for source in self.sources])

        self.log(f"Loaded {len(self.sources)} ImageSource objects.")
        self._ready.set()

    async def _register(self, source: ImageSource) -> None:
        """This function is a coroutine

        Register all endpoints that a ``ImageSource`` can listen
        to and add them to the client listener.

        Parameters
        -----
        source: ``ImageSource``
            The ``ImageSource`` to analyze.
        """
        if not isinstance(source, ImageSource):
            raise TypeError(f"source must be ImageSource, not {source.__class__.__name__}")

        sfw, nsfw = await source._get_all_endpoints()

        for endpoint in sfw:
            if endpoint not in self.sfw:
                self.sfw[endpoint] = []

            self.sfw[endpoint].append(source)

        for endpoint in nsfw:
            if endpoint not in self.nsfw:
                self.nsfw[endpoint] = []

            self.nsfw[endpoint].append(source)

        self.log(f"Loaded {len(sfw)} SFW endpoints and {len(nsfw)} NSFW endpoints from {source}:" + "\nSFW: " + ", ".join(sfw) + "\nNSFW: " + ", ".join(nsfw))

    async def wait_until_ready(self) -> None:
        """This function is a coroutine

        Asynchronously block until all image categories have
        been loaded.
        """
        await self._ready.wait()

    def _check_category(self, category: str, *, mode: Literal["sfw", "nsfw"] = "sfw") -> None:
        if mode not in ("sfw", "nsfw"):
            raise CategoryNotFound(mode)

        if category not in getattr(self, mode):
            raise CategoryNotFound(category)

    async def get(self, category: str, *, mode: Literal["sfw", "nsfw"] = "sfw") -> Optional[str]:
        """This function is a coroutine

        Get a URL from the requested category. If the requested
        category was not registered, this method will raise
        ``CategoryNotFound``.

        Note that although the category was registered, the
        fetching operation may still fail somehow and ``None``
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
        await self.wait_until_ready()
        self._check_category(category, mode=mode)
        image_url = None

        sources: List[ImageSource] = getattr(self, mode)[category]
        random.shuffle(sources)

        for source in sources:
            with contextlib.suppress(aiohttp.ClientError, asyncio.TimeoutError):
                image_url = await source.get(category, mode=mode)

            if image_url:
                return image_url

    async def get_url(self, category: str, *, mode: Literal["sfw", "nsfw"] = "sfw") -> Tuple[str, str]:
        await self.wait_until_ready()
        self._check_category(category, mode=mode)
        source: ImageSource = random.choice(getattr(self, mode)[category])

        return str(source), str(source.get_url(category, mode=mode))
