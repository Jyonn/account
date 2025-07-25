# Generated by Django 2.2.5 on 2019-10-08 13:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('App', '0020_app_create_time'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='app',
            options={'default_manager_name': 'objects'},
        ),
        migrations.AlterModelOptions(
            name='premise',
            options={'default_manager_name': 'objects'},
        ),
        migrations.AlterModelOptions(
            name='scope',
            options={'default_manager_name': 'objects'},
        ),
        migrations.AlterModelOptions(
            name='userapp',
            options={'default_manager_name': 'objects'},
        ),
        migrations.AlterField(
            model_name='app',
            name='create_time',
            field=models.fields.DateTimeField(default=None),
        ),
        migrations.AlterField(
            model_name='app',
            name='desc',
            field=models.fields.CharField(default=None, max_length=32),
        ),
        migrations.AlterField(
            model_name='app',
            name='field_change_time',
            field=models.fields.FloatField(blank=True, default=0, null=True),
        ),
        migrations.AlterField(
            model_name='app',
            name='id',
            field=models.fields.CharField(max_length=32, primary_key=True, serialize=False, verbose_name='应用唯一ID'),
        ),
        migrations.AlterField(
            model_name='app',
            name='logo',
            field=models.fields.CharField(blank=True, default=None, max_length=1024, null=True),
        ),
        migrations.AlterField(
            model_name='app',
            name='name',
            field=models.fields.CharField(max_length=32, unique=True, verbose_name='应用名称'),
        ),
        migrations.AlterField(
            model_name='app',
            name='secret',
            field=models.fields.CharField(max_length=32, verbose_name='应用密钥'),
        ),
        migrations.AlterField(
            model_name='app',
            name='user_num',
            field=models.fields.IntegerField(default=0, verbose_name='用户人数'),
        ),
        migrations.AlterField(
            model_name='premise',
            name='desc',
            field=models.fields.CharField(max_length=20, verbose_name='要求介绍'),
        ),
        migrations.AlterField(
            model_name='premise',
            name='detail',
            field=models.fields.CharField(default=None, max_length=100, verbose_name='要求详细说明'),
        ),
        migrations.AlterField(
            model_name='premise',
            name='name',
            field=models.fields.CharField(max_length=20, unique=True, verbose_name='要求英文简短名称'),
        ),
        migrations.AlterField(
            model_name='scope',
            name='desc',
            field=models.fields.CharField(max_length=20, verbose_name='权限介绍'),
        ),
        migrations.AlterField(
            model_name='scope',
            name='detail',
            field=models.fields.CharField(default=None, max_length=20, verbose_name='权限详细说明'),
        ),
        migrations.AlterField(
            model_name='scope',
            name='name',
            field=models.fields.CharField(max_length=20, unique=True, verbose_name='权限英文简短名称'),
        ),
        migrations.AlterField(
            model_name='userapp',
            name='frequent_score',
            field=models.fields.FloatField(default=0, verbose_name='频繁访问分数，按分值排序为常用应用'),
        ),
        migrations.AlterField(
            model_name='userapp',
            name='last_auth_code_time',
            field=models.fields.CharField(default=None, max_length=20, verbose_name='上一次申请auth_code的时间，防止被多次使用'),
        ),
        migrations.AlterField(
            model_name='userapp',
            name='last_score_changed_time',
            field=models.fields.CharField(default=None, max_length=20, verbose_name='上一次分数变化的时间'),
        ),
        migrations.AlterField(
            model_name='userapp',
            name='mark',
            field=models.fields.PositiveSmallIntegerField(default=0, verbose_name='此用户的打分，0表示没打分'),
        ),
        migrations.AlterField(
            model_name='userapp',
            name='user_app_id',
            field=models.fields.CharField(max_length=16, unique=True, verbose_name='用户在这个app下的唯一ID'),
        ),
    ]
