# Generated by Django 2.0 on 2019-03-06 03:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('User', '0022_user_birthday'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='birthday',
            field=models.DateField(default=None, null=True, verbose_name='生日'),
        ),
    ]
