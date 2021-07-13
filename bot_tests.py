import pytest
from discord.ext import commands
import discord.ext.test as dpytest
import discord

from channels.db import database_sync_to_async

import os

from submissions import models
import bot

@pytest.fixture
async def test_bot(event_loop):
    intents = discord.Intents.default()
    intents.members = True

    test_bot = commands.Bot('!', loop=event_loop, intents=intents)
    test_bot.add_check(bot.globally_block_dms)
    test_bot.add_check(bot.correct_channel)
    test_bot.add_command(bot.submit)
    test_bot.add_command(bot.newweek)

    dpytest.configure(client=test_bot, num_channels=2, num_members=3)

    guild = test_bot.guilds[0]
    submission_channel = guild.text_channels[0]
    os.environ["SUBMISSION_CHANNEL_ID"] = str(submission_channel.id)

    yield test_bot

    await dpytest.empty_queue()

@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_bot_ignores_dms(test_bot):
    guild = test_bot.guilds[0]
    member = guild.members[0]
    dm = await member.create_dm()

    await ignore_discord_error(dpytest.message(content="!help", channel=dm))
    await ignore_discord_error(dpytest.message(content="!submit", channel=dm))
    await ignore_discord_error(dpytest.message(content="!newweek abc", channel=dm))
    assert dpytest.verify().message().nothing()

@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_bot_ignores_other_channels(test_bot):
    guild = test_bot.guilds[0]
    other_channel = guild.text_channels[1]

    await ignore_discord_error(dpytest.message(content="!help", channel=other_channel))
    await ignore_discord_error(dpytest.message(content="!submit", channel=other_channel))
    await ignore_discord_error(dpytest.message(content="!newweek abc", channel=other_channel))
    assert dpytest.verify().message().nothing()

@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_submit_creates_submission(test_bot):
    sender = test_bot.guilds[0].members[0]

    await database_sync_to_async(models.Challenge.objects.create)(week=1, name='week1')
    student = await database_sync_to_async(models.Student.objects.create)(
        discord_snowflake_id=sender.id,
    )

    await dpytest.message(content="!submit 1234", member=sender, attachments=["fake"])

    subm = await database_sync_to_async(models.Submission.objects.first)()
    assert subm.score == 1234
    assert subm.challenge_id == 1
    assert subm.student_id == student.id

@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_submit_requires_attachment(test_bot):
    await database_sync_to_async(models.Challenge.objects.create)(week=1, name='week1')

    with pytest.raises(commands.UserInputError):
        await dpytest.message(content="!submit 1234")
    assert dpytest.verify().message().contains().content("needs one file attachment")

@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_submit_creates_student(test_bot):
    await database_sync_to_async(models.Challenge.objects.create)(week=1, name='week1')

    sender = await make_role_member(test_bot, "Freshman")
    await dpytest.message(content="!submit 1234", member=sender, attachments=["fake"])

    student = await database_sync_to_async(models.Student.objects.get)(discord_snowflake_id=sender.id)
    assert student is not None
    assert student.discord_snowflake_id == sender.id
    assert student.discord_name == f'{sender.name}#{sender.discriminator}'
    assert student.level == models.Student.LevelPlacement.FRESHMAN

@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_submit_updates_student(test_bot):
    new_grad = await make_role_member(test_bot, "Graduate")

    await database_sync_to_async(models.Challenge.objects.create)(week=1, name='week1')
    existing_student = await database_sync_to_async(models.Student.objects.create)(
        discord_snowflake_id=new_grad.id,
        discord_name="xyz#123",
        level=models.Student.LevelPlacement.VARSITY,
    )

    await dpytest.message(content="!submit 1234", member=new_grad, attachments=["fake"])
    student = await database_sync_to_async(models.Student.objects.get)(id=existing_student.id)

    assert student.discord_snowflake_id == new_grad.id
    assert student.discord_name == f'{new_grad.name}#{new_grad.discriminator}'
    assert student.level == models.Student.LevelPlacement.GRADUATE

@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_newweek_creates_given_week(test_bot):
    admin = await make_role_member(test_bot, "Admin")

    await dpytest.message(content="!newweek 3 newnew", member=admin)
    assert dpytest.verify().message().contains().content("Week 3: newnew")

    challenge = await database_sync_to_async(models.Challenge.objects.get)(week=3)
    assert challenge is not None
    assert challenge.name == "newnew"

@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_newweek_creates_next_week(test_bot):
    await database_sync_to_async(models.Challenge.objects.create)(week=1, name='week1')

    admin = await make_role_member(test_bot, "Admin")

    await dpytest.message(content="!newweek anotha one", member=admin)
    assert dpytest.verify().message().contains().content("Week 2: anotha one")

    challenge = await database_sync_to_async(models.Challenge.objects.get)(week=2)
    assert challenge is not None
    assert challenge.name == "anotha one"

@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_newweek_restricted_to_admin(test_bot):
    with pytest.raises(commands.MissingAnyRole):
        await dpytest.message(content="!newweek 1 newnew")
    assert dpytest.verify().message().contains().content("Sorry").content("only faculty, admins, and TOs")

### Helpers

async def ignore_discord_error(coro):
    try:
        await coro
    except discord.DiscordException:
        pass

async def make_role_member(test_bot, role_name, member_index=0):
    guild = test_bot.guilds[member_index]
    role = await guild.create_role(name=role_name)
    member = guild.members[member_index]
    await dpytest.add_role(member, role)

    return member
