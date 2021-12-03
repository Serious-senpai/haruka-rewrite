import asyncio
import re
from typing import Dict, List

import discord
from discord.ext import commands

import leech
from core import bot


class HangmanProgress:

    __slots__ = (
        "_word",
        "life",
        "guessed",
        "incorrect",
    )

    def __init__(self, word: str, *, life: int = 5) -> None:
        self._word: str = word
        self.life: int = life
        self.guessed: List[str] = []
        self.incorrect: List[str] = []

    @property
    def word(self) -> str:
        return self._word

    @property
    def display(self) -> str:
        w: str = ""
        for char in self.word:
            if char in self.guessed:
                w += char
            else:
                w += "-"
        return w


HangmanInProgress: Dict[int, HangmanProgress] = {}


@bot.command(
    name = "hangman",
    description = "Play a hangman game",
    usage = "hangman <initial number of lives | default: 5>",
)
@commands.cooldown(1, 4, commands.BucketType.user)
async def _hangman_cmd(ctx: commands.Context, n: int = 5):
    if n < 1:
        return await ctx.send("Initial number of lives must be greater than 0.")
        
    if n > 15:
        return await ctx.send("Initial number of lives must not exceed 15.")

    if ctx.author.id in HangmanInProgress:
        return await ctx.send("Please complete your ongoing game.")

    word: str = leech.get_word()
    while len(word) < 3:
        word = leech.get_word()

    HangmanInProgress[ctx.author.id] = HangmanProgress(word, life = n)

    em: discord.Embed = discord.Embed(
        title = "Hangman Game",
        description = "-" * len(word) + "\nSend any characters to guess!\nSend `leave` to leave the game.",
        color = 0x2ECC71,
    )
    em.set_author(
        name = f"{ctx.author.name} started Hangman Game!",
        icon_url = ctx.author.avatar.url if ctx.author.avatar else discord.Embed.Empty
    )
    em.set_footer(text = f"💖 {n} left")
    msg: discord.Message = await ctx.send(embed = em)


    def check(message: discord.Message):
        return message.author.id == ctx.author.id and message.channel.id == ctx.channel.id and re.match(r"^\w$", message.content) or message.content.lower() == "leave"


    while ctx.author.id in HangmanInProgress:
        game: HangmanProgress = HangmanInProgress[ctx.author.id]
        try:
            message: discord.Message = await bot.wait_for("message", check = check, timeout = 300.0)
        except asyncio.TimeoutError:
            await ctx.send(f"<@!{ctx.author.id}> timed out for Hangman Game! The answer is **{word}**")
            del HangmanInProgress[ctx.author.id]
            return

        else:
            guess: str = message.content.lower() # len(guess) == 1
            if guess == "leave":
                del HangmanInProgress[ctx.author.id]
                return await ctx.send(f"<@!{ctx.author.id}> left Hangman Game! The answer is **{word}**")

            try:
                await msg.delete()
                await message.delete()
            except:
                pass

            # Construct embed
            em: discord.Embed = discord.Embed(
                title = "Hangman Game",
                color = 0x2ECC71,
            )

            if guess in word:
                game.guessed.append(guess)
                em.set_author(
                    name = f"{ctx.author.name} guessed 1 more character!",
                    icon_url = ctx.author.avatar.url if ctx.author.avatar else discord.Embed.Empty,
                )

            else:
                if not guess in game.incorrect:
                    game.life -= 1
                    game.incorrect.append(guess)
                em.set_author(
                    name = f"{ctx.author.name} guessed incorrectly!",
                    icon_url = ctx.author.avatar.url if ctx.author.avatar else discord.Embed.Empty,
                )

            if game.incorrect:
                em.add_field(
                    name = "Incorrect attempts",
                    value = ", ".join(f"`{w}`" for w in game.incorrect),
                    inline = False,
                )
            em.description = f"{game.display}\nSend any characters to guess!\nSend `leave` to leave the game."
            em.set_footer(text = f"💖 {game.life} left")

            msg = await message.channel.send(embed = em)

            if game.life == 0:
                await message.channel.send(f"<@!{ctx.author.id}> lost Hangman Game! The answer is **{word}**")
                del HangmanInProgress[ctx.author.id]

            if game.display == word:
                await message.channel.send(f"<@!{ctx.author.id}> won Hangman Game! ✨✨")
                del HangmanInProgress[ctx.author.id]
