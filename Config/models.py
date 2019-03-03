""" Adel Liu 180111

系统配置类
"""
from django.db import models

from Base.common import deprint
from Base.validator import field_validator
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

    class __ConfigNone:
        pass

    @classmethod
    def _validate(cls, dict_):
        """验证传入参数是否合法"""
        return field_validator(dict_, Config)

    @classmethod
    def get_config_by_key(cls, key):
        ret = cls._validate(locals())
        if ret.error is not Error.OK:
            return ret

        try:
            o_config = cls.objects.get(key=key)
        except Exception as err:
            deprint(str(err))
            return Ret(Error.NOT_FOUND_CONFIG)
        return Ret(o_config)

    @classmethod
    def get_value_by_key(cls, key, default=__ConfigNone()):
        ret = cls.get_config_by_key(key)
        if ret.error is not Error.OK:
            if isinstance(default, cls.__ConfigNone):
                return ret
            else:
                return Ret(default)
        return Ret(ret.body.value)

    @classmethod
    def update_value(cls, key, value):
        ret = cls._validate(locals())
        if ret.error is not Error.OK:
            return ret

        ret = cls.get_config_by_key(key)
        if ret.error is Error.OK:
            o_config = ret.body
            o_config.value = value
            o_config.save()
            return Ret()

        try:
            o_config = cls(
                key=key,
                value=value,
            )
            o_config.save()
        except Exception as err:
            deprint(str(err))
            return Ret(Error.ERROR_CREATE_CONFIG)

        return Ret(o_config)
