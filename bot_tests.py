import pytest
from discord.ext import commands
import discord.ext.test as dpytest
import discord

from channels.db import database_sync_to_async

import os
os.environ["SUBMISSION_CHANNEL_ID"] = "123"

from submissions import models
import bot

@pytest.fixture
def test_bot(event_loop):
    intents = discord.Intents.default()
    intents.members = True

    test_bot = commands.Bot('!', loop=event_loop, intents=intents)
    test_bot.add_check(bot.globally_block_dms)
    # test_bot.add_check(bot.correct_channel)
    test_bot.add_command(bot.submit)
    test_bot.add_command(bot.newweek)

    dpytest.configure(client=test_bot, num_channels=2, num_members=3)
    return test_bot

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

async def make_role_member(test_bot, role_name, member_index=0):
    guild = test_bot.guilds[member_index]
    role = await guild.create_role(name=role_name)
    member = guild.members[member_index]
    await dpytest.add_role(member, role)

    return member
