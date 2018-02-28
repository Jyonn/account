""" Adel Liu 180111

系统配置类
"""
from django.db import models

from Base.common import deprint
from Base.decorator import field_validator
from Base.error import Error
from Base.response import Ret


class Config(models.Model):
    """
    系统配置，如七牛密钥等
    """
    L = {
        'key': 255,
        'value': 255,
    }
    key = models.CharField(
        max_length=L['key'],
        unique=True,
    )
    value = models.CharField(
        max_length=L['value'],
    )
    FIELD_LIST = ['key', 'value']

    @classmethod
    def _validate(cls, dict_):
        """验证传入参数是否合法"""
        return field_validator(dict_, Config)

    @classmethod
    def get_config_by_key(cls, key):
        ret = cls._validate(locals())
        try:
            o_config = cls.objects.get(key=key)
        except Config.DoesNotExist as err:
            deprint(str(err))
            return Ret(Error.NOT_FOUND_CONFIG)
        except Exception as err:
            deprint(str(err))
            return Ret(Error.NOT_FOUND_CONFIG)
        return Ret(o_config)
