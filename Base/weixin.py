import datetime

import requests
from SmartDjango import E
from django.utils.crypto import get_random_string

from Base.common import sha1
from Config.models import Config, CI

APP_ID = Config.get_value_by_key(CI.WEIXIN_APP_ID)
APP_SECRET = Config.get_value_by_key(CI.WEIXIN_APP_SECRET)


@E.register()
class WeixinError:
    UPDATE_WEIXIN_ACCESS_TOKEN_ERROR = E("更新微信Access Token错误")
    UPDATE_WEIXIN_JSAPI_TICKET_ERROR = E("更新微信JsApi Ticket错误")
    UPDATE_WEIXIN_TIME_NOT_EXPIRED = E("更新间隔太短")


class Weixin:
    @staticmethod
    def update_access_token():
        crt_time = int(datetime.datetime.now().timestamp())
        last_update = int(Config.get_value_by_key(CI.WEIXIN_LAST_UPDATE, '0'))
        if crt_time - last_update < 60 * 80:  # 80 mins
            raise WeixinError.UPDATE_WEIXIN_TIME_NOT_EXPIRED

        resp = requests.get('https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid=%s&secret=%s' % (APP_ID, APP_SECRET))
        data = resp.json()
        resp.close()

        if ('errcode' in data and data['errcode'] != 0) or 'access_token' not in data:
            raise WeixinError.UPDATE_WEIXIN_ACCESS_TOKEN_ERROR
        Config.update_value(CI.WEIXIN_ACCESS_TOKEN, data['access_token'])

        resp = requests.get('https://api.weixin.qq.com/cgi-bin/ticket/getticket?access_token=%s&type=jsapi' % data['access_token'])
        data = resp.json()
        resp.close()

        if ('errcode' in data and data['errcode'] != 0) or 'ticket' not in data:
            raise WeixinError.UPDATE_WEIXIN_JSAPI_TICKET_ERROR
        Config.update_value(CI.WEIXIN_JSAPI_TICKET, data['ticket'])
        Config.update_value(CI.WEIXIN_LAST_UPDATE, str(crt_time))

    @staticmethod
    def get_config(url):
        jsapi_ticket = Config.get_config_by_key(CI.WEIXIN_JSAPI_TICKET)
        noncestr = get_random_string(length=16)
        timestamp = int(datetime.datetime.now().timestamp())
        raw_string = 'jsapi_ticket=%s&noncestr=%s&timestamp=%s&url=%s' % (jsapi_ticket, noncestr, timestamp, url)
        signature = sha1(raw_string)
        return dict(
            noncestr=noncestr,
            signature=signature,
            timestamp=timestamp,
            appid=APP_ID,
        )
