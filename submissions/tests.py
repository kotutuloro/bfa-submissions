from django.test import TestCase
from django.db.utils import IntegrityError

from . import models

class SubmissionTests(TestCase):
    def test_new_submission_uses_latest_challenge(self):
        """
        Use the latest (greatest) week for new submissions by default.
        """

        models.Challenge.objects.create(week=2, name='week2')
        models.Challenge.objects.create(week=1, name='week1')

        student = models.Student.objects.create(
            discord_snowflake_id=99999,
            discord_name='discord#1234',
        )
        subm = student.submission_set.create(score=123)
        self.assertEqual(subm.challenge.week, 2)

class StudentTests(TestCase):
    def setUp(self):
        models.Challenge.objects.create(week=1, name='week1')
        self.student = models.Student.objects.create(
            discord_snowflake_id=99999,
            discord_name='discord#1234',
        )

    def test_save_score_saves_score(self):
        """
        Save a Submission for a Student with the given discord_name.
        """

        self.student.save_score(123, 'url')

        self.assertEqual(self.student.submission_set.count(), 1)
        submission = self.student.submission_set.first()
        self.assertEqual(submission.score, 123)
        self.assertEqual(submission.pic_url, 'url')

    def test_save_score_returns_upscore(self):
        """
        Return the upscore difference between given score and last best score.
        """

        self.student.save_score(100, 'url')
        upscore = self.student.save_score(1000, 'url')
        self.assertEqual(upscore, 900)

    def test_save_score_returns_negative_upscore(self):
        """
        Return the upscore difference between given score and last best score,
        even if the given score is lower.
        """

        self.student.save_score(1000, 'url')
        upscore = self.student.save_score(100, 'url')
        self.assertEqual(upscore, -900)

    def test_save_score_returns_upscore_for_current_week(self):
        """
        Does not use scores from previous weeks.
        """

        self.student.save_score(500, 'url')

        models.Challenge.objects.create(week=2, name='week2')
        self.student.save_score(100, 'url')

        upscore = self.student.save_score(1000, 'url')
        self.assertEqual(upscore, 900)

    def test_save_score_first_submission_returns_none(self):
        """
        Return None if a Student didn't have a previous submission.
        """

        upscore = self.student.save_score(123, 'url')
        self.assertIsNone(upscore)

class ModelHelperTests(TestCase):

    def test_put_student_makes_new_student(self):
        """
        If a Student with the given discord_snowflake_id doesn't already exist,
        create one and return it.
        """

        self.assertEqual(models.Student.objects.count(), 0)
        student = models.put_student(
            99999,
            discord_name='discord#1234',
            level=models.LevelPlacement.FRESHMAN,
        )

        self.assertEqual(models.Student.objects.count(), 1)
        self.assertEqual(student, models.Student.objects.first())

        self.assertEqual(student.discord_snowflake_id, 99999)
        self.assertEqual(student.discord_name, 'discord#1234')
        self.assertEqual(student.level, models.LevelPlacement.FRESHMAN)

    def test_put_student_uses_existing_student(self):
        """
        If a Student with the given discord_snowflake_id already exists,
        update and return it.
        """

        models.Student.objects.create(
            discord_snowflake_id=99999,
            discord_name='discord#1234',
            ddr_name='DDR',
            twitter='abcddd',
            level=models.LevelPlacement.VARSITY,
        )
        self.assertEqual(models.Student.objects.count(), 1)

        student = models.put_student(
            99999,
            discord_name='newname#1234',
            level=models.LevelPlacement.GRADUATE,
            twitter='wow',
        )
        self.assertEqual(models.Student.objects.count(), 1)
        self.assertEqual(student, models.Student.objects.first())

        self.assertEqual(student.discord_snowflake_id, 99999)
        self.assertEqual(student.discord_name, 'newname#1234')
        self.assertEqual(student.level, models.LevelPlacement.GRADUATE)
        self.assertEqual(student.ddr_name, 'DDR')
        self.assertEqual(student.twitter, 'wow')

    def test_new_week_creates_challenge(self):
        """
        Create and return a challenge with the provided week and name.
        """

        new_challenge = models.new_week(3, 'testweek')
        self.assertEqual(new_challenge.week, 3)
        self.assertEqual(new_challenge.name, 'testweek')
        self.assertTrue(new_challenge.is_open)

        self.assertEqual(models.Challenge.objects.get(week=3), new_challenge)

    def test_new_week_uses_latest_week_if_no_week(self):
        """
        Uses the latest week if provided week is None.
        """

        # latest week
        models.Challenge.objects.create(week=7, name='week2')

        new_challenge = models.new_week(None, 'testweek')
        self.assertEqual(new_challenge.week, 8) # latest + 1

    def test_new_week_closes_previous_week(self):
        """
        Sets latest week's is_open field to False
        """

        # latest week
        models.Challenge.objects.create(week=7, name='week2')

        models.new_week(None, 'testweek')

        last_challenge = models.Challenge.objects.get(week=7)
        self.assertFalse(last_challenge.is_open)

    def test_new_week_raises_exception_for_duplicate_week(self):
        """
        Raises a django IntegrityError if the week already exists
        """

        models.Challenge.objects.create(week=1, name='week1')
        with self.assertRaises(IntegrityError):
            models.Challenge.objects.create(week=1, name="anotha one")
