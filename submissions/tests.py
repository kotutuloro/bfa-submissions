from django.test import TestCase

from . import models

class ModelHelperTests(TestCase):
    def setUp(self):
        models.Challenge.objects.create(week=1, name='week1')

    def test_new_submission_uses_latest_challenge(self):
        """
        Use the latest week for new submissions by default.
        """

        models.Challenge.objects.create(week=2, name='week2')

        student = models.Student.objects.create(discord_id='discord#1234')
        subm = student.submission_set.create(score=123)
        self.assertEqual(subm.challenge.week, 2)

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
            ['<Submission: 123 for discord#1234>']
        )

    def test_save_score_returns_upscore(self):
        """
        Return the upscore difference between given score and last best score.
        """

        models.save_score('discord#1234', 100, 'url')
        upscore = models.save_score('discord#1234', 1000, 'url')
        self.assertEqual(upscore, 900)

    def test_save_score_first_submission_returns_none(self):
        """
        Returns None if a Student didn't have a previous submission.
        """

        upscore = models.save_score('discord#1234', 123, 'url')
        self.assertIsNone(upscore)
