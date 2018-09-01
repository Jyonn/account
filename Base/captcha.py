import json

from geetest import GeetestLib

from Base.common import deprint
from Base.session import Session
from Config.models import Config

GEETEST_ID = Config.get_value_by_key('geetest-id', 'YOUR-GEETEST-ID').body
GEETEST_KEY = Config.get_value_by_key('geetest-key', 'YOUR-GEETEST-KEY').body
GT = GeetestLib(GEETEST_ID, GEETEST_KEY)


class Captcha:
    @staticmethod
    def get(request):
        status = GT.pre_process()
        deprint('status', status)
        if not status:
            status = 2
        deprint('status', status)
        Session.save(request, GT.GT_STATUS_SESSION_KEY, status)
        deprint(Session.load(request, GT.GT_STATUS_SESSION_KEY))
        return json.loads(GT.get_response_str())

    @staticmethod
    def verify(request, challenge, validate, seccode):
        deprint(Session.load(request, GT.GT_STATUS_SESSION_KEY))
        try:
            status = Session.load(request, GT.GT_STATUS_SESSION_KEY)
            if status == 1:
                result = GT.success_validate(challenge, validate, seccode)
            else:
                result = GT.failback_validate(challenge, validate, seccode)
        except Exception as err:
            deprint(str(err))
            return False
        return True if result else False
