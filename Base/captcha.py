from geetest import GeetestLib

from Base import session
from Config.models import Config

GEETEST_ID = Config.get_value_by_key('geetest-id', 'YOUR-GEETEST-ID').body
GEETEST_KEY = Config.get_value_by_key('geetest-key', 'YOUR-GEETEST-KEY').body
GT = GeetestLib(GEETEST_ID, GEETEST_KEY)


class Captcha:
    @staticmethod
    def get(request):
        status = GT.pre_process()
        if not status:
            status = 2
        session.save_session(request, GT.GT_STATUS_SESSION_KEY, status)
        return GT.get_response_str()

    @staticmethod
    def verify(request, challenge, validate, seccode):
        status = session.load_session(request, GT.GT_STATUS_SESSION_KEY)
        if status == 1:
            result = GT.success_validate(challenge, validate, seccode)
        else:
            result = GT.failback_validate(challenge, validate, seccode)
        print(result)
        return True if result else False
