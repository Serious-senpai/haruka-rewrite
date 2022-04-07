import random


with open("./bot/assets/misc/fact.txt", "r", encoding="utf-8") as f:
    facts = [row.strip("\n") for row in f.readlines()]


def get_fact() -> str:
    return random.choice(facts)


with open("./bot/assets/misc/8ball.txt", "r", encoding="utf-8") as f:
    answers = [row.strip("\n") for row in f.readlines()]


def get_8ball() -> str:
    return random.choice(answers)
