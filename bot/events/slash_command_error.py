import traceback

import discord

import slash
from core import bot


@bot.event
async def on_slash_command_error(interaction: discord.Interaction, error: Exception):
    if isinstance(error, slash.NoPrivateMessage):
        await interaction.response.send_message("This command can only be invoked in a server channel.")

    elif isinstance(error, slash.CommandInvokeError):
        await on_slash_command_error(interaction, error.original)

    else:
        try:
            await interaction.followup.send("...")
        except BaseException:
            bot.log("An exception occurred when trying to send a notification message:")
            bot.log(traceback.format_exc())
        else:
            bot.log("Notification message was successfully sent.")

        bot.log("".join(traceback.format_exception(error.__class__, error, error.__traceback__)))
        await bot.report("An error has just occured and was handled by `on_slash_command_error`", send_state=False)
