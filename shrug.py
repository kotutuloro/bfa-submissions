import os

import discord
from discord.ext import commands

description = '''my guy

i actually do not know yet lol
'''

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

@bot.command(help="i do submission things")
async def submit(ctx, score: int):
    print(f'rcvd cmd: {ctx.message}')
    pic_url = validate_attachment(ctx.message)
    await ctx.send(f'{ctx.author.mention} your stuff: {pic_url}')

@submit.error
async def invalid_submission(ctx, error):
    if isinstance(error, commands.UserInputError):
        await ctx.send(f'print help or something {ctx.author.mention}')
        await ctx.send_help()

def validate_attachment(msg):
    if len(msg.attachments) != 1:
        raise commands.BadArgument
    attachment = msg.attachments[0]
    if attachment.height is None or attachment.width is None:
        raise commands.BadArgument

    return attachment.proxy_url


bot.run(token)
