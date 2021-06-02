""" Adel Liu 180111

系统配置类
"""
from SmartDjango import models, E


@E.register(id_processor=E.idp_cls_prefix())
class ConfigError:
    CREATE_CONFIG = E("更新配置错误")
    CONFIG_NOT_FOUND = E("不存在的配置")


class Config(models.Model):
    """
    系统配置，如七牛密钥等
    """
    key = models.CharField(
        max_length=255,
        unique=True,
    )
    value = models.CharField(
        max_length=255,
    )

    @classmethod
    def get_config_by_key(cls, key):
        cls.validator(locals())

        try:
            config = cls.objects.get(key=key)
        except cls.DoesNotExist as err:
            raise ConfigError.CONFIG_NOT_FOUND(debug_message=err)

        return config

    @classmethod
    def get_value_by_key(cls, key, default=None):
        try:
            config = cls.get_config_by_key(key)
            return config.value
        except Exception:
            return default

    @classmethod
    def update_value(cls, key, value):
        cls.validator(locals())

        try:
            config = cls.get_config_by_key(key)
            config.value = value
            config.save()
        except E as e:
            if e.eis(ConfigError.CONFIG_NOT_FOUND):
                try:
                    config = cls(
                        key=key,
                        value=value,
                    )
                    config.save()
                except Exception as err:
                    raise ConfigError.CREATE_CONFIG(debug_message=err)
            else:
                raise e
        except Exception as err:
            raise ConfigError.CREATE_CONFIG(debug_message=err)


class ConfigInstance:
    HOST = 'host'
    JWT_ENCODE_ALGO = 'jwt-encode-algo'
    PROJECT_SECRET_KEY = 'project-secret-key'

    QCLOUD_APP_ID = 'qcloud-app-id'
    QCLOUD_SECRET_ID = 'qcloud-secret-id'
    QCLOUD_SECRET_KEY = 'qcloud-secret-key'

    SENDER_EMAIL = 'sender-email'
    SENDER_EMAIL_PWD = 'sender-email-pwd'
    SMTP_SERVER = 'smtp-server'
    SMTP_PORT = 'smtp-port'

    LAST_RE_FREQ_SCORE_DATE = 'last-refresh-frequent-score-date'

    QINIU_ACCESS_KEY = 'qiniu-access-key'
    QINIU_SECRET_KEY = 'qiniu-secret-key'
    RES_BUCKET = 'qiniu-res-bucket'
    PUBLIC_BUCKET = 'qiniu-public-bucket'
    RES_CDN_HOST = 'res-cdn-host'
    PUBLIC_CDN_HOST = 'public-cdn-host'

    G_RECAPTCHA_SECRET = 'g-recaptcha-secret'

    WEIXIN_APP_ID = 'weixin-app-id'
    WEIXIN_APP_SECRET = 'weixin-app-secret'
    WEIXIN_LAST_UPDATE = 'weixin-last-update'
    WEIXIN_ACCESS_TOKEN = 'weixin-access-token'
    WEIXIN_JSAPI_TICKET = 'weixin-jsapi-ticket'

    YUNPIAN_APPKEY = 'yunpian-appkey'


CI = ConfigInstance
