import random

from discord import app_commands
from youtube_dl import utils

from _types import Interaction
from core import bot


class _RandomGeneratorSlash(app_commands.Group):
    @app_commands.command(name="user-agent", description="Generate a random User-Agent header")
    async def _user_agent_slash(self, interaction: Interaction):
        await interaction.response.send_message("```\n" + utils.random_user_agent() + "\n```")

    @app_commands.command(name="number", description="Generate a random number in the [0, 1) range")
    async def _number_slash(self, interaction: Interaction):
        await interaction.response.send_message(random.random())


bot.tree.add_command(_RandomGeneratorSlash(name="random", description="Random generator"))
