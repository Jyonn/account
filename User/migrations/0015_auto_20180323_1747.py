# Generated by Django 2.0 on 2018-03-23 17:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('User', '0014_user_qitian'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='qitian',
            field=models.CharField(default=None, max_length=20, unique=True),
        ),
    ]