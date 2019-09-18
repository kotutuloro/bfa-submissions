from django.db import models
from django.utils import timezone

class Student(models.Model):
    # primary key: id (auto set by django)
    discord_id = models.CharField(
        'discord username and discriminator, eg tropikiko#7800',
        max_length=40,
        unique=True,
        blank=True,
        null=True,
        )
    dancer_name = models.CharField(
        'in-game ddr dancer name',
        max_length=8,
        blank=True,
        )
    twitter = models.CharField(
        'twitter handle',
        max_length=20,
        blank=True,
        )
    alum = models.BooleanField(
        'alumnus / upperclassman',
        null=True,
        )

class Submission(models.Model):
    # primary key: id (auto set by django)
    student = models.ForeignKey(
        Student,
        on_delete=models.PROTECT,
        )
    score = models.PositiveIntegerField()
    pic_url = models.URLField(
        'url to the picture for the submission',
        )
    submitted_at = models.DateTimeField(
        'time submission was added to the database',
        auto_now_add=True,
        )
