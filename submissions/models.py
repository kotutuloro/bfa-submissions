from django.db import models
from django.utils import timezone
from channels.db import database_sync_to_async

class Student(models.Model):

    class LevelPlacement(models.TextChoices):
        JUNIOR_VARSITY = 'JV'
        FRESHMAN = 'FR'
        VARSITY = 'VA'
        GRADUATE = 'GR'
        UNKNOWN = ''

    # primary key: id (auto set by django)
    discord_id = models.CharField(
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
        'division',
        max_length=2,
        choices=LevelPlacement.choices,
        default=LevelPlacement.UNKNOWN,
    )

    def __str__(self):
        return f'discord: {self.discord_id} | ddr: {self.ddr_name or None}'

class Challenge(models.Model):
    week = models.PositiveIntegerField(
        primary_key=True
    )
    name = models.TextField()

    def __str__(self):
        return f'Week {self.week}: {self.name}'

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
    submitted_at = models.DateTimeField(
        'submission time',
        auto_now_add=True,
    )

    def __str__(self):
        return f'{self.score} for {self.student.discord_id or self.student.ddr_name}'


@database_sync_to_async
def async_save_score(discord_id, score, pic_url):
    return save_score(discord_id, score, pic_url)

def save_score(discord_id, score, pic_url):
    """Adds new Submission for a Student. Returns score diff from best submission.

    Gets or creates a Student for the given discord_id.
    Adds Submission for that student, and returns the difference between the
    given score and the previous best submission if it exists.
    Returns None if this is the first submission.
    """

    student = Student.objects.get_or_create(discord_id=discord_id)[0]
    highest_subm = student.submission_set.filter(
        challenge=Challenge.latest_week()
        ).order_by('score').last()
    new_subm = student.submission_set.create(score=score, pic_url=pic_url)

    if highest_subm is not None:
        return new_subm.score - highest_subm.score

    return

@database_sync_to_async
def async_new_week(week, name):
    return new_week(week, name)

def new_week(week, name):
    """Creates a new challenge. If week is None, uses latest week + 1."""

    if week is None:
        week = Challenge.latest_week() + 1

    return Challenge.objects.create(week=week, name=name)
