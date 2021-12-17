import asyncio
import traceback
from typing import Dict

import discord
from discord.ext import commands

from core import bot


COOLDOWN_NOTIFY: Dict[int, Dict[str, bool]] = {}


@bot.event
async def on_command_error(ctx: commands.Context, error: Exception):
    if isinstance(error, commands.CommandNotFound):
        return

    elif isinstance(error, commands.CommandOnCooldown):
        if await bot.is_owner(ctx.author):
            return await ctx.reinvoke()

        if ctx.author.id not in COOLDOWN_NOTIFY:
            COOLDOWN_NOTIFY[ctx.author.id] = {
                ctx.command.name: True,
            }
        else:
            if not COOLDOWN_NOTIFY[ctx.author.id].get(ctx.command.name, False):
                COOLDOWN_NOTIFY[ctx.author.id][ctx.command.name] = True
            else:
                return

        time: str = ""
        seconds: float = error.retry_after

        days: int = int(seconds / 86400)
        seconds -= days * 86400

        hours: int = int(seconds / 3600)
        seconds -= hours * 3600

        minutes: int = int(seconds / 60)
        seconds -= minutes * 60

        if days > 0:
            time += f" {days}d"
        if hours > 0:
            time += f" {hours}h"
        if minutes > 0:
            time += f" {minutes}m"
        if seconds > 0:
            time += " {:.2f}s".format(seconds)

        time: str = time.strip()

        await ctx.send(
            f"⏱️ <@!{ctx.author.id}> This command is on cooldown!\nYou can use it after **{time}**!",
            delete_after=max(1.0, error.retry_after) if error.retry_after < 600 else None,
        )

        await asyncio.sleep(error.retry_after)
        COOLDOWN_NOTIFY[ctx.author.id][ctx.command.name] = False

    elif isinstance(error, commands.UserInputError):
        await ctx.send_help(ctx.command)

    # These are the subclasses of commands.CheckFailure
    elif isinstance(error, commands.NotOwner):
        return

    elif isinstance(error, commands.NoPrivateMessage):
        await ctx.send("This command can only be invoked in a server channel.")

    elif isinstance(error, commands.BotMissingPermissions):
        await ctx.send("🚫 I do not have permission to execute this command: " + ", ".join(f"`{perm}`" for perm in error.missing_permissions))

    elif isinstance(error, commands.MissingPermissions):
        await ctx.send("🚫 You do not have the permission to invoke this command: " + ", ".join(f"`{perm}`" for perm in error.missing_permissions))

    elif isinstance(error, commands.NSFWChannelRequired):
        await ctx.send("🔞 This command can only be invoked in a NSFW channel.")

    elif isinstance(error, commands.CheckFailure):
        return

    elif isinstance(error, commands.CommandInvokeError):
        await on_command_error(ctx, error.original)

    # Other exceptions
    elif isinstance(error, discord.Forbidden):
        return

    elif isinstance(error, discord.DiscordServerError):
        return

    else:
        try:
            await ctx.send("...")
        except BaseException:
            bot.log("An exception occurred when trying to send a notification message:")
            bot.log(traceback.format_exc())
        else:
            bot.log("Notification message was successfully sent.")

        bot.log(f"'{ctx.message.content}' in {ctx.guild}/{ctx.channel} from {ctx.author} ({ctx.author.id}):")
        bot.log("".join(traceback.format_exception(error.__class__, error, error.__traceback__)))
        await bot.report("An error has just occured and was handled by `on_command_error`", send_state=False)
