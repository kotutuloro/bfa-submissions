from django.db import models
from django.utils import timezone

class Student(models.Model):
    # primary key: id (auto set by django)
    discord_id = models.CharField(
        help_text='discord username and discriminator (eg: tropikiko#7800)',
        max_length=40,
        unique=True,
        blank=True,
        null=True,
        )
    dancer_name = models.CharField(
        'ddr dancer name',
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

    def __str__(self):
        return f'discord: {self.discord_id} | ddr: {self.dancer_name or None}'

class Submission(models.Model):
    # primary key: id (auto set by django)
    student = models.ForeignKey(
        Student,
        on_delete=models.PROTECT,
        )
    score = models.PositiveIntegerField()
    pic_url = models.URLField(
        'submission picture url',
        )
    submitted_at = models.DateTimeField(
        'submission time',
        auto_now_add=True,
        )

    def __str__(self):
        return f'{self.score} for {self.student.discord_id or self.student.dancer_name}'
