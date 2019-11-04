import json
from urllib.parse import urlencode

import requests
from django.utils.crypto import get_random_string

from Base.session import Session
from Config.models import Config, CI

yunpian_appkey = Config.get_value_by_key(CI.YUNPIAN_APPKEY)


class SendMobile:
    REGISTER = 0
    FIND_PWD = 1
    LOGIN = 2

    CHINA = 0
    ABROAD = 1
    texts = [
        [
            '【六七九】本次注册的验证码为#code#，五分钟内有效。',
            '【六七九】本次密码找回的验证码为#code#，五分钟内有效。',
            '【六七九】本次登录的验证码为#code#，五分钟内有效。',
        ], [
            '【Six79】Code for registering is #code#, valid within 5 minutes.',
            '【Six79】Code for retrieving password is #code#, valid within 5 minutes.',
            '【Six79】Code for logging in is #code#, valid within 5 minutes.',
        ]
    ]
    PHONE = 'phone'
    PHONE_NUMBER = 'phone_number'
    QITIAN_ID = 'qitian_id'
    LOGIN_TYPE = 'login_type'

    @staticmethod
    def send_captcha(request, mobile, type_):
        if type_ < 0 or type_ > 2:
            return
        if mobile.startswith('+86'):
            region = SendMobile.CHINA
        else:
            region = SendMobile.ABROAD
        text = SendMobile.texts[region][type_]
        code = get_random_string(length=6, allowed_chars="1234567890")
        text = text.replace("#code#", code)

        SendMobile._send_sms(yunpian_appkey, text, mobile)
        Session.save_captcha(request, SendMobile.PHONE, code)
        Session.save(request, SendMobile.PHONE_NUMBER, mobile)

    @staticmethod
    def check_captcha(request, code):
        Session.check_captcha(request, SendMobile.PHONE, code)
        phone = Session.load(request, SendMobile.PHONE_NUMBER)
        return phone

    @staticmethod
    def _send_sms(apikey, text, mobile):
        """
        云片短信发送API
        :param apikey: 云片应用密钥
        :param text: 发送明文
        :param mobile: 11位手机号
        :return:
        """
        # 服务地址
        url = "https://sms.yunpian.com/v2/sms/single_send.json"
        params = urlencode({'apikey': apikey, 'text': text, 'mobile': mobile})
        headers = {
            "Content-type": "application/x-www-form-urlencoded",
            "Accept": "application/json"
        }
        response = requests.post(url, params, headers=headers)
        response_str = response.text
        response.close()
        return json.loads(response_str)

# print(SendMobile.send_captcha("17816871961"))
