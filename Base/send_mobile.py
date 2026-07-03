from django.utils.crypto import get_random_string
from notificator import Notificator

from Base.session import Session
from Config.models import Config, CI


class SendMobile:
    REGISTER = 0
    FIND_PWD = 1
    LOGIN = 2

    CAPTCHA_EXPIRE_MINUTES = 5

    PHONE = 'phone'
    PHONE_NUMBER = 'phone_number'
    QITIAN_ID = 'qitian_id'
    LOGIN_TYPE = 'login_type'

    @staticmethod
    def send_captcha(request, mobile, type_):
        if type_ < 0 or type_ > 2:
            return

        code = get_random_string(length=6, allowed_chars='1234567890')
        SendMobile._send_sms(mobile, code)
        Session.save_captcha(request, SendMobile.PHONE, code)
        Session.save(request, SendMobile.PHONE_NUMBER, mobile)

    @staticmethod
    def check_captcha(request, code):
        Session.check_captcha(request, SendMobile.PHONE, code)
        phone = Session.load(request, SendMobile.PHONE_NUMBER)
        return phone

    @staticmethod
    def _send_sms(mobile, code):
        notificator = Notificator(
            name=Config.get_value_by_key(CI.NOTIFICATOR_NAME),
            token=Config.get_value_by_key(CI.NOTIFICATOR_TOKEN),
            host=Config.get_value_by_key(CI.NOTIFICATOR_HOST),
        )

        return notificator.prepare_sms(mobile).send(
            format='verification',
            body={
                'code': code,
                'time': SendMobile.CAPTCHA_EXPIRE_MINUTES,
            },
        )
