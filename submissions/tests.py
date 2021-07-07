from django.test import TestCase
from django.db.utils import IntegrityError

from . import models

class ModelTests(TestCase):
    def test_new_submission_uses_latest_challenge(self):
        """
        Use the latest (greatest) week for new submissions by default.
        """

        models.Challenge.objects.create(week=2, name='week2')
        models.Challenge.objects.create(week=1, name='week1')

        student = models.Student.objects.create(discord_id='discord#1234')
        subm = student.submission_set.create(score=123)
        self.assertEqual(subm.challenge.week, 2)

class ModelHelperTests(TestCase):
    def setUp(self):
        models.Challenge.objects.create(week=1, name='week1')

    def test_save_score_saves_score(self):
        """
        Save a Submission for a Student with the given discord_id.
        """

        models.save_score('discord#1234', 123, 'url')
        student = models.Student.objects.get(discord_id='discord#1234')
        self.assertEqual(student.submission_set.count(), 1)
        submission = student.submission_set.first()
        self.assertEqual(submission.score, 123)
        self.assertEqual(submission.pic_url, 'url')

    def test_save_score_makes_new_student(self):
        """
        If a Student with the given discord_id doesn't already exist,
        create one and use it.
        """

        self.assertEqual(models.Student.objects.count(), 0)

        models.save_score('discord#1234', 123, 'url')
        self.assertEqual(models.Student.objects.count(), 1)
        self.assertEqual(
            models.Student.objects.first().discord_id,
            'discord#1234'
        )

        student = models.Student.objects.first()
        submission = student.submission_set.first()
        self.assertEqual(submission.score, 123)
        self.assertEqual(submission.pic_url, 'url')

    def test_save_score_uses_existing_student(self):
        """
        If a Student with the given discord_id already exists, use it.
        """

        models.Student.objects.create(
            discord_id='discord#1234',
            ddr_name="DDR"
        )
        self.assertEqual(models.Student.objects.count(), 1)

        models.save_score('discord#1234', 123, 'url')
        self.assertEqual(models.Student.objects.count(), 1)

        student = models.Student.objects.first()
        self.assertEqual(student.ddr_name, 'DDR')
        self.assertQuerysetEqual(
            student.submission_set.all(),
            ['<Submission: 123 for discord#1234>'],
            transform=repr
        )

    def test_save_score_returns_upscore(self):
        """
        Return the upscore difference between given score and last best score.
        """

        models.save_score('discord#1234', 100, 'url')
        upscore = models.save_score('discord#1234', 1000, 'url')
        self.assertEqual(upscore, 900)

    def test_save_score_returns_negative_upscore(self):
        """
        Return the upscore difference between given score and last best score,
        even if the given score is lower.
        """

        models.save_score('discord#1234', 1000, 'url')
        upscore = models.save_score('discord#1234', 100, 'url')
        self.assertEqual(upscore, -900)

    def test_save_score_returns_upscore_for_current_week(self):
        """
        Does not use scores from previous weeks.
        """

        models.save_score('discord#1234', 500, 'url')

        models.Challenge.objects.create(week=2, name='week2')
        models.save_score('discord#1234', 100, 'url')

        upscore = models.save_score('discord#1234', 1000, 'url')
        self.assertEqual(upscore, 900)

    def test_save_score_first_submission_returns_none(self):
        """
        Return None if a Student didn't have a previous submission.
        """

        upscore = models.save_score('discord#1234', 123, 'url')
        self.assertIsNone(upscore)

    def test_new_week_creates_challenge(self):
        """
        Create and return a challenge with the provided week and name.
        """

        new_challenge = models.new_week(3, 'testweek')
        self.assertEqual(new_challenge.week, 3)
        self.assertEqual(new_challenge.name, 'testweek')

        self.assertEqual(models.Challenge.objects.get(week=3), new_challenge)

    def test_new_week_uses_latest_week_if_no_week(self):
        """
        Uses the latest week if provided week is None.
        """

        # latest week
        models.Challenge.objects.create(week=7, name='week2')

        new_challenge = models.new_week(None, 'testweek')
        self.assertEqual(new_challenge.week, 8) # latest + 1

    def test_new_week_raises_exception_for_duplicate_week(self):
        """
        Raises a django IntegrityError if the week already exists
        """

        with self.assertRaises(IntegrityError):
            models.Challenge.objects.create(week=1, name="anotha one")
