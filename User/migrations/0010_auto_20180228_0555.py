# Generated by Django 2.0 on 2018-02-28 05:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('User', '0009_auto_20171216_2135'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='user',
            name='grant',
        ),
        migrations.RemoveField(
            model_name='user',
            name='parent',
        ),
        migrations.AddField(
            model_name='user',
            name='region',
            field=models.IntegerField(default=1),
        ),
    ]