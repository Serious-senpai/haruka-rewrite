import json
import random
from typing import List, Optional

import bs4
import discord

import _nhentai
from core import bot


with open("./bot/assets/misc/wordlist.txt", "r", encoding="utf-8") as f:
    wordlist: List[str] = [row.strip("\n") for row in f.readlines()]


def get_word() -> str:
    return random.choice(wordlist)


with open("./bot/assets/misc/fact.txt", "r", encoding="utf-8") as f:
    facts: List[str] = [row.strip("\n") for row in f.readlines()]


def get_fact() -> str:
    return random.choice(facts)


with open("./bot/assets/misc/miku-api.json", "r", encoding="utf-8") as f:
    miku_files: List[str] = json.load(f)["files"]


def get_miku() -> str:
    return random.choice(miku_files)


with open("./bot/assets/misc/8ball.txt", "r", encoding="utf-8") as f:
    answers: List[str] = [row.strip("\n") for row in f.readlines()]


def get_8ball() -> str:
    return random.choice(answers)


with open("./bot/assets/misc/quote.txt", "r", encoding="utf-8") as f:
    quotes: List[str] = [row.strip("\n") for row in f.readlines()]


def get_quote() -> str:
    return random.choice(quotes)


async def get_sauce(src) -> List[discord.Embed]:
    ret: List[discord.Embed] = []
    async with bot.session.post("https://saucenao.com/search.php", data={"url": src}) as response:
        if response.ok:
            html: str = await response.text(encoding="utf-8")
            soup: bs4.BeautifulSoup = bs4.BeautifulSoup(html, "html.parser")
            results: bs4.element.ResultSet[bs4.BeautifulSoup] = soup.find_all(name="div", class_="result")
            count: int = 1

            for result in results:
                if len(ret) == 6:
                    break

                try:
                    if "hidden" in result.get("class"):
                        break

                    result = result.find(
                        name="table",
                        attrs={"class": "resulttable"}
                    )

                    image_url: str = result.find(
                        name="div",
                        attrs={"class": "resultimage"}
                    ).find(name="img").get("src")

                    url: str = result.find(
                        name="div",
                        attrs={"class": "resultcontentcolumn"}
                    ).find(name="a").get("href")

                    similarity: str = result.find(
                        name="div",
                        attrs={"class": "resultsimilarityinfo"}
                    ).get_text()

                    em: discord.Embed = discord.Embed(
                        title=f"Displaying result #{count}",
                        color=0x2ECC71,
                    )
                    em.add_field(
                        name="Sauce",
                        value=url,
                        inline=False,
                    )
                    em.add_field(
                        name="Similarity",
                        value=similarity,
                        inline=False,
                    )
                    em.set_thumbnail(url=image_url)
                    ret.append(em)
                    count += 1
                except BaseException:
                    continue
            return ret

        return ret


async def search_nhentai(query: str) -> Optional[List[_nhentai.NHentaiSearch]]:
    params = {
        "q": query,
    }
    async with bot.session.get("https://nhentai.net/search/", params=params) as response:
        if response.ok:
            html: str = await response.text(encoding="utf-8")
            soup: bs4.BeautifulSoup = bs4.BeautifulSoup(html, "html.parser")
            container: bs4.BeautifulSoup = soup.find("div", attrs={"class": "container index-container"})
            # Even when no result is found and the page
            # displays 404, the response status is still
            # 200 so another check is necessary.
            if not container:
                return
            doujins: bs4.element.ResultSet[bs4.BeautifulSoup] = container.find_all("div", attrs={"class": "gallery"})
            return list(_nhentai.NHentaiSearch(doujin) for doujin in doujins)
        else:
            return


async def get_nhentai(id: int) -> Optional[_nhentai.NHentai]:
    async with bot.session.get(f"https://nhentai.net/g/{id}") as response:
        if response.ok:
            html: str = await response.text(encoding="utf-8")
            soup: bs4.BeautifulSoup = bs4.BeautifulSoup(html, "html.parser")
            return _nhentai.NHentai(soup)
        else:
            return
