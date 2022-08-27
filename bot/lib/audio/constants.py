import aiohttp


TIMEOUT = aiohttp.ClientTimeout(total=15)
INVIDIOUS_URLS = [
    "https://invidious.snopyta.org",
    "https://invidio.xamh.de",
    "https://yewtu.be",
    "https://vid.puffyan.us",
    "https://invidious-us.kavin.rocks",
    "https://inv.riverside.rocks",
    "https://vid.mint.lgbt",
    "https://invidious-jp.kavin.rocks",
    "https://invidious.osi.kr",
    "https://yt.artemislena.eu",
    "https://youtube.076.ne.jp",
    "https://invidious.namazso.eu",
    "https://invidious.kavin.rocks",
]


def set_priority(instance: str) -> None:
    try:
        INVIDIOUS_URLS.remove(instance)
    except ValueError as exc:
        raise ValueError(f"No instance with name {instance}") from exc
    else:
        INVIDIOUS_URLS.insert(0, instance)
