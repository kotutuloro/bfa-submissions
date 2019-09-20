import os

import discord
from discord.ext import commands

from submissions.models import save_score

description = 'A bot to help with weekly score submissions'
bot = commands.Bot(command_prefix='!', description=description)

token = os.getenv('DISCORD_BOT_TOKEN')
submission_channel_id = int(os.getenv('SUBMISSION_CHANNEL_ID'))


@bot.event
async def on_ready():
    print("It's lit")
    print(f'Logged in as {bot.user}')
    print('~*~*~*~*~*~*~*~')

@bot.check
async def correct_channel(ctx):
    submission_channel = bot.get_channel(submission_channel_id)
    return ctx.channel == submission_channel

@bot.command()
async def submit(ctx, score: int):
    """Submit a score **with picture** for the BFA Weekly Challenge

    This command requires a photo attachment to be part of the message.

    <score> -- Your ex or money score (depending on the challenge) [digits only, no commas]
    """

    print(f'rcvd cmd: {ctx.message}')
    pic_url = validate_attachment(ctx.message)
    upscore = save_score(str(ctx.author), score, pic_url)

    message = f"Submitted {ctx.author.mention}'s score of {score}"
    if upscore is not None:
        message = f'{message}\n+[{upscore}]!'

    await ctx.send(message)

@submit.error
async def invalid_submission(ctx, error):
    if isinstance(error, commands.UserInputError):
        await ctx.send(f'Incorrect command usage: {error}')
        await ctx.send_help(submit)
    else:
        print(f'Error occurred: {error}')
        await ctx.send(f":grimacing: {ctx.author.mention}'s submission did not go through. Please try again.")

def validate_attachment(msg):
    """Checks if a message includes 1 image attachment

    Returns the image's proxy_url
    """

    if len(msg.attachments) != 1:
        raise commands.TooManyArguments('needs one file attachment.')
    attachment = msg.attachments[0]
    if attachment.height is None or attachment.width is None:
        raise commands.BadArgument('file attachment must be an image.')

    return attachment.proxy_url

if __name__ == '__main__':
    bot.run(token)
