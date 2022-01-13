import asyncio
import traceback

import discord
from discord.ext import commands

import utils
from core import bot


bot.owner_bypass = True
COOLDOWN_NOTIFY = {}


@bot.event
async def on_command_error(ctx: commands.Context, error: Exception):
    if isinstance(error, commands.CommandNotFound):
        return

    elif isinstance(error, commands.CommandOnCooldown):
        if bot.owner_bypass and await bot.is_owner(ctx.author):
            await ctx.reinvoke()
            return

        if ctx.author.id not in COOLDOWN_NOTIFY:
            COOLDOWN_NOTIFY[ctx.author.id] = {}

        if not COOLDOWN_NOTIFY[ctx.author.id].get(ctx.command.name, False):
            COOLDOWN_NOTIFY[ctx.author.id][ctx.command.name] = True
        else:
            return

        await ctx.send(f"⏱️ <@!{ctx.author.id}> This command is on cooldown!\nYou can use it after **{utils.format(error.retry_after)}**!")

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
        bot.log(f"'{ctx.message.content}' in {ctx.message.id}/{ctx.channel.id} from {ctx.author} ({ctx.author.id}):")
        bot.log("".join(traceback.format_exception(error.__class__, error, error.__traceback__)))
        await bot.report("An error has just occured and was handled by `on_command_error`", send_state=False)
