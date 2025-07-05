import datetime

from qcloud_image import Client
from qcloud_image import CIUrls
from smartdjango import Error

from Config.models import Config, CI

APP_ID = Config.get_value_by_key(CI.QCLOUD_APP_ID)
SECRET_ID = Config.get_value_by_key(CI.QCLOUD_SECRET_ID)
SECRET_KEY = Config.get_value_by_key(CI.QCLOUD_SECRET_KEY)

BUCKET = 'BUCKET'
client = Client(APP_ID, SECRET_ID, SECRET_KEY, BUCKET)
client.use_http()
client.set_timeout(30)


@Error.register
class IDCardErrors:
    IDCARD_DETECT_ERROR = Error("身份证自动验证错误")
    REAL_VERIFIED = Error("已实名认证")
    CARD_NOT_COMPLETE = Error("身份证正反面照片没有完善")
    CARD_VALID_EXPIRED = Error("身份证认证过期")
    AUTO_VERIFY_FAILED = Error("自动实名认证失败，请尝试人工认证")
    VERIFYING = Error("您已提交认证")


class IDCard:
    @staticmethod
    def detect_front(link):
        resp = client.idcard_detect(CIUrls([link]), 0)
        if resp['httpcode'] != 200:
            raise IDCardErrors.IDCARD_DETECT_ERROR(resp['result_list'][0]['message'])
        resp = resp['result_list'][0]
        if resp['code'] != 0:
            raise IDCardErrors.IDCARD_DETECT_ERROR('验证错误' + str(resp['msg']))
        resp = resp['data']

        try:
            birth = datetime.datetime.strptime(resp['birth'], '%Y/%m/%d').strftime('%Y-%m-%d')
        except Exception as err:
            raise IDCardErrors.IDCARD_DETECT_ERROR('生日验证错误', debug_message=err)

        return dict(
            male=resp['sex'] == '男',
            name=resp['name'],
            idcard=resp['id'],
            birthday=birth,
        )

    @staticmethod
    def detect_back(link):
        resp = client.idcard_detect(CIUrls([link]), 1)
        if resp['httpcode'] != 200:
            raise IDCardErrors.IDCARD_DETECT_ERROR(resp['result_list'][0]['message'])
        resp = resp['result_list'][0]
        if resp['code'] != 0:
            raise IDCardErrors.IDCARD_DETECT_ERROR('验证错误' + str(resp['msg']))
        resp = resp['data']
        try:
            valid_start = datetime.datetime.strptime(
                resp['valid_date'][:10], '%Y.%m.%d').strftime('%Y-%m-%d')
            valid_end = datetime.datetime.strptime(
                resp['valid_date'][-10:], '%Y.%m.%d').strftime('%Y-%m-%d')
        except Exception as err:
            raise IDCardErrors.IDCARD_DETECT_ERROR('生日验证错误', debug_message=err)

        return dict(
            valid_start=valid_start,
            valid_end=valid_end,
        )
