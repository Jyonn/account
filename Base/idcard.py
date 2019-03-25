import datetime

from qcloud_image import Client
from qcloud_image import CIUrls

from Base.common import deprint
from Base.error import Error
from Base.response import Ret
from Config.models import Config

APP_ID = Config.get_value_by_key('qcloud-app-id', 'YOUR-APP-ID').body
SECRET_ID = Config.get_value_by_key('qcloud-secret-id', 'YOUR-SECRET-ID').body
SECRET_KEY = Config.get_value_by_key('qcloud-secret-key', 'YOUR-SECRET-KEY').body

BUCKET = 'BUCKET'
client = Client(APP_ID, SECRET_ID, SECRET_KEY, BUCKET)
client.use_http()
client.set_timeout(30)


class IDCard:
    @staticmethod
    def detect_front(link):
        resp = client.idcard_detect(CIUrls([link]), 0)
        if resp['httpcode'] != 200:
            return Ret(Error.IDCARD_DETECT_ERROR, append_msg='，网络错误' + str(resp['httpcode']))
        resp = resp['result_list'][0]
        if resp['code'] != 0:
            return Ret(Error.IDCARD_DETECT_ERROR, append_msg='，验证错误' + str(resp['msg']))
        resp = resp['data']

        try:
            birth = datetime.datetime.strptime(resp['birth'], '%Y/%m/%d').strftime('%Y-%m-%d')
        except Exception as err:
            deprint(str(err))
            return Ret(Error.IDCARD_DETECT_ERROR, append_msg='，生日验证错误')

        return Ret(dict(
            nation=resp['nation'],
            address=resp['address'],
            male=resp['sex'] == '男',
            name=resp['name'],
            idcard=resp['id'],
            birthday=birth,
        ))

    @staticmethod
    def detect_back(link):
        resp = client.idcard_detect(CIUrls([link]), 1)
        if resp['httpcode'] != 200:
            return Ret(Error.IDCARD_DETECT_ERROR, append_msg='，网络错误' + str(resp['httpcode']))
        resp = resp['result_list'][0]
        if resp['code'] != 0:
            return Ret(Error.IDCARD_DETECT_ERROR, append_msg='，验证错误' + str(resp['msg']))
        resp = resp['data']
        try:
            valid_start = datetime.datetime.strptime(resp['valid_date'][:10], '%Y.%m.%d').strftime('%Y-%m-%d')
            valid_end = datetime.datetime.strptime(resp['valid_date'][-10:], '%Y.%m.%d').strftime('%Y-%m-%d')
        except Exception as err:
            deprint(str(err))
            return Ret(Error.IDCARD_DETECT_ERROR, append_msg='，生日验证错误')

        return Ret(dict(
            authority=resp['authority'],
            valid_start=valid_start,
            valid_end=valid_end,
        ))
