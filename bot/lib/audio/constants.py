import aiohttp


TIMEOUT = aiohttp.ClientTimeout(total=15)
with open("./bot/assets/misc/iv_instances.txt", "r", encoding="utf-8") as f:
    INVIDIOUS_URLS = ["https://" + instance.strip("\n") for instance in f.readlines()]


def set_priority(instance: str) -> None:
    try:
        INVIDIOUS_URLS.remove(instance)
    except ValueError as exc:
        raise ValueError(f"No instance with name {instance}") from exc
    else:
        INVIDIOUS_URLS.insert(0, instance)
