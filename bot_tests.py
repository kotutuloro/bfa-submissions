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
    test_bot.add_command(bot.addtwitter)
    test_bot.add_command(bot.addname)
    test_bot.add_command(bot.newweek)
    test_bot.add_command(bot.close)
    test_bot.add_command(bot.reopen)

    dpytest.configure(client=test_bot, num_channels=2, num_members=3)

    guild = test_bot.guilds[0]
    submission_channel = guild.text_channels[0]
    os.environ["SUBMISSION_CHANNEL_ID"] = str(submission_channel.id)

    yield test_bot

    await dpytest.empty_queue()

### Bot checks

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

### General commands

@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_submit_creates_submission(test_bot):
    sender = await make_role_member(test_bot, "Freshman")

    await database_sync_to_async(models.Challenge.objects.create)(week=1, name='week1')
    student = await database_sync_to_async(models.Student.objects.create)(
        discord_snowflake_id=sender.id,
        level=models.LevelPlacement.FRESHMAN,
    )

    await dpytest.message(content="!submit 1234", member=sender, attachments=["fake"])

    subm = await database_sync_to_async(models.Submission.objects.first)()
    assert subm.score == 1234
    assert subm.challenge_id == 1
    assert subm.student_id == student.id
    assert subm.level == student.level

@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_submit_requires_attachment(test_bot):
    await database_sync_to_async(models.Challenge.objects.create)(week=1, name='week1')

    with pytest.raises(commands.UserInputError):
        await dpytest.message(content="!submit 1234")
    assert dpytest.verify().message().contains().content("needs one file attachment")

@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_submit_requires_positive_score(test_bot):
    await database_sync_to_async(models.Challenge.objects.create)(week=1, name='week1')

    with pytest.raises(commands.UserInputError):
        await dpytest.message(content="!submit -1", attachments=["fake"])
    assert dpytest.verify().message().contains().content("score must be between")

@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_submit_requires_less_than_mfc(test_bot):
    await database_sync_to_async(models.Challenge.objects.create)(week=1, name='week1')

    with pytest.raises(commands.UserInputError):
        await dpytest.message(content="!submit 1000001", attachments=["fake"])
    assert dpytest.verify().message().contains().content("score must be between")

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
    assert student.level == models.LevelPlacement.FRESHMAN

@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_submit_updates_student(test_bot):
    new_grad = await make_role_member(test_bot, "Graduate")

    await database_sync_to_async(models.Challenge.objects.create)(week=1, name='week1')
    existing_student = await database_sync_to_async(models.Student.objects.create)(
        discord_snowflake_id=new_grad.id,
        discord_name="xyz#123",
        level=models.LevelPlacement.VARSITY,
    )

    await dpytest.message(content="!submit 1234", member=new_grad, attachments=["fake"])
    student = await database_sync_to_async(models.Student.objects.get)(id=existing_student.id)

    assert student.discord_snowflake_id == new_grad.id
    assert student.discord_name == f'{new_grad.name}#{new_grad.discriminator}'
    assert student.level == models.LevelPlacement.GRADUATE

    subm = await database_sync_to_async(models.Submission.objects.first)()
    assert subm.level == models.LevelPlacement.GRADUATE

@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_submit_not_allowed_during_closed_submissions(test_bot):
    await database_sync_to_async(models.Challenge.objects.create)(week=1, name='week1', is_open=False)

    with pytest.raises(commands.DisabledCommand):
        await dpytest.message(content="!submit 1234", attachments=["fake"])
    assert dpytest.verify().message().contains().content("currently closed")
    assert await database_sync_to_async(models.Submission.objects.count)() == 0

@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_addtwitter_creates_student(test_bot):
    sender = await make_role_member(test_bot, "Varsity")
    await dpytest.message(content="!addtwitter my_cool_twitter", member=sender)

    student = await database_sync_to_async(models.Student.objects.get)(discord_snowflake_id=sender.id)
    assert student is not None
    assert student.discord_snowflake_id == sender.id
    assert student.discord_name == f'{sender.name}#{sender.discriminator}'
    assert student.level == models.LevelPlacement.VARSITY
    assert student.twitter == "my_cool_twitter"
    assert dpytest.verify().message().contains().content("Updated")

@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_addtwitter_updates_student(test_bot):
    sender = await make_role_member(test_bot, "Graduate")
    existing_student = await database_sync_to_async(models.Student.objects.create)(
        discord_snowflake_id=sender.id,
        discord_name="xyz#123",
        level=models.LevelPlacement.VARSITY,
        twitter="lesscooltwitter",
    )

    await dpytest.message(content="!addtwitter my_cool_twitter", member=sender)
    student = await database_sync_to_async(models.Student.objects.get)(id=existing_student.id)

    assert student.discord_snowflake_id == sender.id
    assert student.discord_name == f'{sender.name}#{sender.discriminator}'
    assert student.level == models.LevelPlacement.GRADUATE
    assert student.twitter == "my_cool_twitter"
    assert dpytest.verify().message().contains().content("Updated")

@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_addname_creates_student(test_bot):
    sender = await make_role_member(test_bot, "JV")
    await dpytest.message(content="!addname DDRCOOL", member=sender)

    student = await database_sync_to_async(models.Student.objects.get)(discord_snowflake_id=sender.id)
    assert student is not None
    assert student.discord_snowflake_id == sender.id
    assert student.discord_name == f'{sender.name}#{sender.discriminator}'
    assert student.level == models.LevelPlacement.JUNIOR_VARSITY
    assert student.ddr_name == "DDRCOOL"
    assert dpytest.verify().message().contains().content("Updated")

@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_addname_updates_student(test_bot):
    sender = await make_role_member(test_bot, "Freshman")
    existing_student = await database_sync_to_async(models.Student.objects.create)(
        discord_snowflake_id=sender.id,
        discord_name="xyz#123",
        level=models.LevelPlacement.JUNIOR_VARSITY,
        ddr_name="LESSCOOL",
    )

    await dpytest.message(content="!addname DDRCOOL", member=sender)
    student = await database_sync_to_async(models.Student.objects.get)(id=existing_student.id)

    assert student.discord_snowflake_id == sender.id
    assert student.discord_name == f'{sender.name}#{sender.discriminator}'
    assert student.level == models.LevelPlacement.FRESHMAN
    assert student.ddr_name == "DDRCOOL"
    assert dpytest.verify().message().contains().content("Updated")

### Faculty/Admin commands

@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_newweek_creates_next_week(test_bot):
    await database_sync_to_async(models.Challenge.objects.create)(week=1, name='week1', is_open=False)

    admin = await make_role_member(test_bot, "Admin")

    await dpytest.message(content="!newweek anotha one", member=admin)
    assert dpytest.verify().message().contains().content("Week 2: anotha one")

    challenge = await database_sync_to_async(models.Challenge.objects.get)(week=2)
    assert challenge is not None
    assert challenge.name == "anotha one"

@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_newweek_not_allowed_during_opened_submissions(test_bot):
    await database_sync_to_async(models.Challenge.objects.create)(week=1, name='week1', is_open=True)

    admin = await make_role_member(test_bot, "Admin")
    await dpytest.message(content="!newweek nope", member=admin)
    assert dpytest.verify().message().contains().content("still open")

    c = await database_sync_to_async(models.Challenge.objects.filter(week=2).count)()
    assert c == 0

@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_newweek_restricted_to_admin(test_bot):
    await database_sync_to_async(models.Challenge.objects.create)(week=1, name='week1', is_open=False)

    with pytest.raises(commands.MissingAnyRole):
        await dpytest.message(content="!newweek 1 newnew")
    assert dpytest.verify().message().contains().content("Sorry").content("only faculty, admins, and TOs")

@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_close_closes_submissions(test_bot):
    await database_sync_to_async(models.Challenge.objects.create)(week=1, name='week1', is_open=True)
    admin = await make_role_member(test_bot, "Admin")

    await dpytest.message(content="!close", member=admin)
    assert dpytest.verify().message().contains().content("Week 1:").content("now closed")

    challenge = await database_sync_to_async(models.Challenge.objects.get)(week=1)
    assert not challenge.is_open

    # test that submissions fail
    with pytest.raises(commands.DisabledCommand):
        await dpytest.message(content="!submit 1234", attachments=["fake"])
    assert await database_sync_to_async(models.Submission.objects.count)() == 0

@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_close_restricted_to_admin(test_bot):
    with pytest.raises(commands.MissingAnyRole):
        await dpytest.message(content="!close")
    assert dpytest.verify().message().contains().content("Sorry").content("only faculty, admins, and TOs")

@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_reopen_reopens_submissions(test_bot):
    await database_sync_to_async(models.Challenge.objects.create)(week=1, name='week1', is_open=False)
    admin = await make_role_member(test_bot, "Admin")

    await dpytest.message(content="!reopen", member=admin)
    assert dpytest.verify().message().contains().content("Week 1:").content("now reopen")

    challenge = await database_sync_to_async(models.Challenge.objects.get)(week=1)
    assert challenge.is_open

    # test that submissions go through
    await dpytest.message(content="!submit 1234", attachments=["fake"])
    assert await database_sync_to_async(models.Submission.objects.count)() == 1

@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_reopen_restricted_to_admin(test_bot):
    with pytest.raises(commands.MissingAnyRole):
        await dpytest.message(content="!reopen")
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
