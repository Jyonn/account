# Generated by Django 2.0 on 2019-03-01 13:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('App', '0011_auto_20180423_1818'),
    ]

    operations = [
        migrations.AddField(
            model_name='userapp',
            name='frequent_score',
            field=models.FloatField(default=0, verbose_name='频繁访问分数，按分值排序为常用应用'),
        ),
        migrations.AddField(
            model_name='userapp',
            name='last_score_changed_time',
            field=models.CharField(default=None, max_length=20, verbose_name='上一次分数变化的时间'),
        ),
    ]