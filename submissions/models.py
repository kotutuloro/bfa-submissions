from django.db import models
from django.utils import timezone
from channels.db import database_sync_to_async

class LevelPlacement(models.TextChoices):
    JUNIOR_VARSITY = 'JV'
    FRESHMAN = 'FR'
    VARSITY = 'VA'
    GRADUATE = 'GR'
    UNKNOWN = ''

class Student(models.Model):
    # primary key: id (auto set by django)
    discord_snowflake_id = models.BigIntegerField(
        unique=True,
    )
    discord_name = models.CharField(
        help_text='discord username and discriminator (eg: tropikiko#7800)',
        max_length=40,
        unique=True,
        blank=True,
        null=True,
    )
    ddr_name = models.CharField(
        max_length=8,
        blank=True,
    )
    twitter = models.CharField(
        'twitter handle',
        max_length=20,
        blank=True,
    )
    level = models.CharField(
        'division (most recent)',
        max_length=2,
        choices=LevelPlacement.choices,
        default=LevelPlacement.UNKNOWN,
    )

    def __str__(self):
        return f'discord: {self.discord_name} | ddr: {self.ddr_name or "<unknown>"}'

    def save_score(self, score, pic_url):
        """Adds new Submission for a Student. Returns score diff from best submission.

        Adds Submission for given student, and returns the difference between the
        given score and the previous best submission if it exists.
        Returns None if this is the first submission.
        """

        highest_subm = self.top_score(Challenge.latest_week())
        new_subm = self.submission_set.create(score=score, pic_url=pic_url, level=self.level)

        if highest_subm is not None:
            return new_subm.score - highest_subm.score

        return

    def top_score(self, week):
        return self.submission_set.filter(challenge=week).order_by('score').last()

class Challenge(models.Model):
    week = models.PositiveIntegerField(
        primary_key=True
    )
    name = models.TextField()
    is_open = models.BooleanField(default=True)

    def __str__(self):
        return f'Week {self.week}: {self.name}'

    def open(self):
        self.is_open = True
        self.save()

    def close(self):
        self.is_open = False
        self.save()

    @classmethod
    def latest_week(cls):
        """Find the latest challenge week."""

        try:
            latest = cls.objects.latest()
            return latest.week
        except cls.DoesNotExist:
            return

    class Meta:
        get_latest_by = 'week'

class Submission(models.Model):
    # primary key: id (auto set by django)
    student = models.ForeignKey(
        Student,
        on_delete=models.PROTECT,
    )
    challenge = models.ForeignKey(
        Challenge,
        on_delete=models.PROTECT,
        default=Challenge.latest_week,
    )
    score = models.PositiveIntegerField()
    pic_url = models.URLField(
        'submission picture url',
    )
    level = models.CharField(
        'division (at submission time)',
        max_length=2,
        choices=LevelPlacement.choices,
        default=LevelPlacement.UNKNOWN,
    )
    submitted_at = models.DateTimeField(
        'submission time',
        auto_now_add=True,
    )

    def __str__(self):
        return f'{self.score} for {self.student.discord_name or self.student.ddr_name}'

@database_sync_to_async
def async_save_score(discord_snowflake_id, discord_name, level, score, pic_url):
    student = put_student(
        discord_snowflake_id,
        discord_name=discord_name,
        level=level,
    )
    return student.save_score(score, pic_url)

@database_sync_to_async
def async_update_student(discord_snowflake_id, **kwargs):
    return put_student(discord_snowflake_id, **kwargs)

def put_student(discord_snowflake_id, **kwargs):
    student, _ = Student.objects.update_or_create(
        discord_snowflake_id=discord_snowflake_id,
        defaults=kwargs
    )
    return student

@database_sync_to_async
def async_new_week(name):
    return new_week(name)

def new_week(name):
    """Creates a new challenge using latest week + 1.
    """

    latest = Challenge.latest_week() or 0
    week = latest + 1
    return Challenge.objects.create(week=week, name=name)

@database_sync_to_async
def close_submissions():
    latest = Challenge.latest_week()
    if latest:
        c = Challenge.objects.get(week=latest)
        c.close()
        return c

@database_sync_to_async
def reopen_submissions():
    latest = Challenge.latest_week()
    if latest:
        c = Challenge.objects.get(week=latest)
        c.open()
        return c

@database_sync_to_async
def is_latest_week_open():
    latest = Challenge.latest_week()
    if latest:
        c = Challenge.objects.get(week=latest)
        return c.is_open
    return False
