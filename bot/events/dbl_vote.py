import topgg

from core import bot


@bot.event
async def on_dbl_vote(data: topgg.types.BotVoteData):
    await bot.report(
        "An user has just voted!",
        send_log=False,
        send_state=False,
    )
