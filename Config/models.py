from django.db import models
from smartdjango import Error

from Config.validators import ConfigValidator, ConfigErrors


class Config(models.Model):
    vldt = ConfigValidator

    key = models.CharField(
        max_length=vldt.MAX_KEY_LENGTH,
        unique=True,
        validators=[vldt.key],
    )

    value = models.CharField(
        max_length=vldt.MAX_VALUE_LENGTH,
        validators=[vldt.value],
    )

    @classmethod
    def get_config_by_key(cls, key) -> 'Config':
        try:
            return cls.objects.get(key=key)
        except cls.DoesNotExist as err:
            raise ConfigErrors.NOT_FOUND(details=err)

    @classmethod
    def get_value_by_key(cls, key, default=None):
        try:
            return cls.get_config_by_key(key).value
        except Exception:
            return default

    @classmethod
    def update_value(cls, key, value):
        try:
            config = cls.get_config_by_key(key)
            config.value = value
            config.save()
        except Error as e:
            if e == ConfigErrors.NOT_FOUND:
                try:
                    config = cls(
                        key=key,
                        value=value,
                    )
                    config.save()
                except Exception as err:
                    raise ConfigErrors.CREATE(details=err)
            else:
                raise e
        except Exception as err:
            raise ConfigErrors.CREATE(details=err)


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
