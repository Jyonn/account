import datetime

import requests
from django.utils.crypto import get_random_string

from Base.common import sha1
from Base.error import Error
from Base.response import Ret
from Config.models import Config

APP_ID = Config.get_value_by_key('weixin-app-id', 'YOUR-APP-ID').body
APP_SECRET = Config.get_value_by_key('weixin-app-secret', 'YOUR-APP-SECRET').body


class Weixin:
    @staticmethod
    def update_access_token():
        crt_time = int(datetime.datetime.now().timestamp())
        last_update = int(Config.get_value_by_key('weixin-last-update', '0').body)
        if crt_time - last_update < 60 * 80:  # 80 mins
            return Ret(Error.UPDATE_WEIXIN_TIME_NOT_EXPIRED)

        resp = requests.get('https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid=%s&secret=%s' % (APP_ID, APP_SECRET))
        data = resp.json()
        resp.close()

        if ('errcode' in data and data['errcode'] != 0) or 'access_token' not in data:
            return Ret(Error.UPDATE_WEIXIN_ACCESS_TOKEN_ERROR)
        ret = Config.update_value('weixin-access-token', data['access_token'])
        if ret.error is not Error.OK:
            return ret

        resp = requests.get('https://api.weixin.qq.com/cgi-bin/ticket/getticket?access_token=%s&type=jsapi' % data['access_token'])
        data = resp.json()
        resp.close()

        if ('errcode' in data and data['errcode'] != 0) or 'ticket' not in data:
            return Ret(Error.UPDATE_WEIXIN_JSAPI_TICKET_ERROR)
        ret = Config.update_value('weixin-jsapi-ticket', data['ticket'])
        if ret.error is not Error.OK:
            return ret

        Config.update_value('weixin-last-update', str(crt_time))

        return Ret()

    @staticmethod
    def get_config(url):
        ret = Config.get_config_by_key('weixin-jsapi-ticket')
        if ret.error is not Error.OK:
            return ret
        jsapi_ticket = ret.body.value
        noncestr = get_random_string(length=16)
        timestamp = int(datetime.datetime.now().timestamp())
        raw_string = 'jsapi_ticket=%s&noncestr=%s&timestamp=%s&url=%s' % (jsapi_ticket, noncestr, timestamp, url)
        signature = sha1(raw_string)
        print(raw_string, signature)
        return Ret(dict(
            noncestr=noncestr,
            signature=signature,
            timestamp=timestamp,
            appid=APP_ID,
        ))
