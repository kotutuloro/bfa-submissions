import os
import typing

from discord.ext import commands
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bfa.settings')
django.setup()

from submissions.models import (
    async_save_score,
    async_update_student,
    async_new_week,
    close_submissions,
    reopen_submissions,
    is_latest_week_open,
    Student,
)

DIVISIONS = Student.LevelPlacement

description = 'A bot to help with weekly score submissions'
bot = commands.Bot(command_prefix='!', description=description)


@bot.event
async def on_ready():
    print("It's lit")
    print(f'Logged in as {bot.user}')
    print('~*~*~*~*~*~*~*~')

@bot.check
async def globally_block_dms(ctx):
    return ctx.guild is not None

@bot.check
async def correct_channel(ctx):
    """Checks that message is posted in the correct channel before proceeding."""

    return ctx.channel.id == int(os.getenv('SUBMISSION_CHANNEL_ID'))

@bot.before_invoke
async def print_command(ctx):
    print(f'received {ctx.invoked_with} cmd: "{ctx.message.clean_content}" {ctx.message}')


async def are_submissions_open(ctx):
    """Checks that submissions are open before proceeding."""

    if await is_latest_week_open():
        return True
    else:
        raise commands.DisabledCommand

@bot.command()
@commands.check(are_submissions_open)
async def submit(ctx, score: int):
    """Submit a score **with picture** for the BFA Weekly Challenge

    This command requires a photo attachment to be part of the message.

    <score> -- Your ex or money score (depending on the challenge) [digits only, no commas]
    """

    pic_url = validate_attachment(ctx.message)
    div = get_division(ctx.author.roles)
    upscore = await async_save_score(ctx.author.id, str(ctx.author), div, score, pic_url)

    message = f"Submitted {ctx.author.mention}'s score of {score}"

    if upscore is not None:
        if upscore < 0:
            message = f"{message}\nThis is {abs(upscore)} lower than your highest submission this week, but I saved the photo just in case."
        else:
            message = f'{message}\n+{upscore} upscore!'

    await ctx.send(message)

@submit.error
async def invalid_submission(ctx, error):
    if isinstance(error, commands.DisabledCommand):
        await ctx.send(f'Sorry {ctx.author.mention}, submissions are currently closed.')
    elif isinstance(error, commands.UserInputError):
        await ctx.send(f'Incorrect command usage: {error}')
        await ctx.send_help(submit)
    else:
        await generic_on_error(ctx, error)

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

@bot.command()
async def addtwitter(ctx, twitter):
    """Add twitter username to your Student profile

    <twitter> -- Your twitter username
    """

    div = get_division(ctx.author.roles)
    await async_update_student(
        ctx.author.id,
        discord_name=str(ctx.author),
        level=div,
        twitter=twitter,
    )
    await ctx.send(f"Updated {ctx.author.mention}'s profile!")

@bot.command()
async def addname(ctx, ddr_name):
    """Add DDR name to your Student profile

    <ddr_name> -- Your DDR name (ex. KEEKSTER)
    """

    div = get_division(ctx.author.roles)
    await async_update_student(
        ctx.author.id,
        discord_name=str(ctx.author),
        level=div,
        ddr_name=ddr_name,
    )
    await ctx.send(f"Updated {ctx.author.mention}'s profile!")

@addtwitter.error
@addname.error
async def invalid_update(ctx, error):
    if isinstance(error, commands.UserInputError):
        await ctx.send(f'Incorrect command usage: {error}')
        await ctx.send_help(ctx.command)
    else:
        await generic_on_error(ctx, error)

def get_division(roles_list):
    """Finds the highest division in a given list of Roles.

    Returns the code for that division based on Student.LevelPlacement choices.
    """

    divs = {
        'Graduate': DIVISIONS.GRADUATE,
        'Varsity': DIVISIONS.VARSITY,
        'Freshman': DIVISIONS.FRESHMAN,
        'JV': DIVISIONS.JUNIOR_VARSITY,
    }

    role_names = {role.name for role in roles_list}
    for div, code in divs.items():
        if div in role_names:
            return code
    return DIVISIONS.UNKNOWN

@bot.command()
@commands.has_any_role('Admin', 'Faculty', 'TO')
async def newweek(ctx, week: typing.Optional[int], *, name):
    """Start a new weekly challenge

    [week] -- **Optional** Week number (defaults to the greatest existing week + 1)
    <name> -- Name of the new weekly challenge
    """

    try:
        challenge = await async_new_week(week, name)
    except django.db.utils.IntegrityError:
        await ctx.send(f'{ctx.author.mention} Week number {week} already exists!')
    else:
        await ctx.send(f'Week {challenge.week}: {challenge.name} has begun!')

@bot.command()
@commands.has_any_role('Admin', 'Faculty', 'TO')
async def close(ctx):
    """Close submissions for the current weekly challenge"""

    challenge = await close_submissions()
    if challenge is not None:
        await ctx.send(f'Pencils down! Submissions for Week {challenge.week}: {challenge.name} are now closed!')
    else:
        await ctx.send("(There's no challenge week to close.)")

@bot.command()
@commands.has_any_role('Admin', 'Faculty', 'TO')
async def reopen(ctx):
    """Reopen submissions for the current weekly challenge"""

    challenge = await reopen_submissions()
    if challenge is not None:
        await ctx.send(f'Submissions for Week {challenge.week}: {challenge.name} are now reopen!')
    else:
        await ctx.send("(There's no challenge week to reopen.)")

@newweek.error
@close.error
@reopen.error
async def invalid_restricted(ctx, error):
    if isinstance(error, commands.UserInputError):
        await ctx.send(f'Incorrect command usage: {error}')
        await ctx.send_help(ctx.command)
    elif isinstance(error, commands.MissingAnyRole):
        await ctx.send(f'Sorry {ctx.author.mention}, only faculty, admins, and TOs can use that command!')
    else:
        await generic_on_error(ctx, error)

async def generic_on_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        # it's either in a dm or in the wrong channel, in which case the bot
        # should stay silent.
        pass
    else:
        print(f'Error occurred in `{ctx.command}`: {error.__class__.__name__}: {error}')
        await ctx.send(f":grimacing: An error occurred running that command! Please try again {ctx.author.mention}.")
        raise error

if __name__ == '__main__':
    # ensure necessary env vars are set
    os.environ['SUBMISSION_CHANNEL_ID']
    token = os.environ['DISCORD_BOT_TOKEN']
    bot.run(token)
