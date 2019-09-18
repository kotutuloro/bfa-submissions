# Generated by Django 2.2.5 on 2019-09-18 19:55

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Student',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('discord_id', models.CharField(blank=True, max_length=40, null=True, unique=True, verbose_name='discord username and discriminator, eg tropikiko#7800')),
                ('dancer_name', models.CharField(blank=True, max_length=8, verbose_name='in-game ddr dancer name')),
                ('twitter', models.CharField(blank=True, max_length=20, verbose_name='twitter handle')),
                ('alum', models.BooleanField(null=True, verbose_name='alumnus / upperclassman')),
            ],
        ),
        migrations.CreateModel(
            name='Submission',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('score', models.PositiveIntegerField()),
                ('pic_url', models.URLField(verbose_name='url to the picture for the submission')),
                ('submitted_at', models.DateTimeField(auto_now_add=True, verbose_name='time submission was added to the database')),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='submissions.Student')),
            ],
        ),
    ]
