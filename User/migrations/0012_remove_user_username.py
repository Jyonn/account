# Generated by Django 2.0 on 2018-03-10 19:42

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('User', '0011_auto_20180228_1939'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='user',
            name='username',
        ),
    ]
