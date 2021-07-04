import os

import discord
from discord.ext import commands

import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bfa.settings')
django.setup()

from submissions.models import async_save_score

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
    """Checks that message is posted in the correct channel before proceeding."""

    submission_channel = bot.get_channel(submission_channel_id)
    return ctx.channel == submission_channel

@bot.command()
async def submit(ctx, score: int):
    """Submit a score **with picture** for the BFA Weekly Challenge

    This command requires a photo attachment to be part of the message.

    <score> -- Your ex or money score (depending on the challenge) [digits only, no commas]
    """

    print(f'received cmd: {ctx.message}')
    pic_url = validate_attachment(ctx.message)
    upscore = await async_save_score(str(ctx.author), score, pic_url)

    message = f"Submitted {ctx.author.mention}'s score of {score}"

    if upscore < 0:
        message = f"{message}\nThis is {abs(upscore)} lower than your highest submission this week, but I saved the photo just in case."
    elif upscore is not None:
        message = f'{message}\n+[{upscore}] upscore!'

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
