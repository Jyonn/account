import json
from urllib.parse import urlencode

import requests
from django.utils.crypto import get_random_string

from Config.models import Config

yunpian_appkey = Config.get_value_by_key('yunpian-appkey')


class SendMobile:
    REGISTER = 0
    FORGET_PASSWORD = 1
    CHINA = 0
    ABROAD = 1
    texts = [
        [
            '【六七九】本次注册的验证码为#code#，五分钟内有效。',
            '【六七九】本次密码找回的验证码为#code#，五分钟内有效。'
        ], [
            '【Six79】Code for registering is #code#, valid within 5 minutes.',
            '【Six79】Code for retrieving password is #code#, valid within 5 minutes.',
        ]
    ]

    @staticmethod
    def send_captcha(mobile, type_):
        if mobile.startswith('+86'):
            region = SendMobile.CHINA
        else:
            region = SendMobile.ABROAD
        text = SendMobile.texts[region][type_]
        code = get_random_string(length=6, allowed_chars="1234567890")
        text = text.replace("#code#", code)
        SendMobile.send_sms(yunpian_appkey, text, mobile)
        return code

    @staticmethod
    def send_sms(apikey, text, mobile):
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
        headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "application/json"}
        response = requests.post(url, params, headers=headers)
        response_str = response.text
        response.close()
        # print(response_str)
        return json.loads(response_str)

# print(SendMobile.send_captcha("17816871961"))
