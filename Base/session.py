"""180228 Adel Liu

用于滑动验证码，手机验证码
"""

import datetime

from smartdjango import Error


@Error.register
class SessionErrors:
    CAPTCHA = Error("验证失败")
    CAPTCHA_EXPIRED = Error("验证码过期，请重试")
    SESSION = Error("会话错误，请刷新重试")


class Session:
    @staticmethod
    def save(request, key, value, visit_time=-1):
        request.session["saved_" + key] = value
        request.session["saved_" + key + "_visit_time"] = visit_time

    @staticmethod
    def load(request, key, once_delete=True):
        visit_time = request.session.get("saved_" + key + "_visit_time")
        if visit_time is None:
            return None
        if visit_time == 0:
            del request.session["saved_" + key + "_visit_time"]
        value = request.session.get("saved_" + key)
        if value is None:
            return None
        if visit_time == 0:
            del request.session["saved_" + key]
            return None
        if once_delete:
            del request.session["saved_" + key]
        request.session["saved_" + key + "_visit_time"] = visit_time - 1
        return value

    @staticmethod
    def save_captcha(request, captcha_type, code, last=300):
        request.session["saved_" + captcha_type + "_code"] = str(code)
        request.session["saved_" + captcha_type + "_time"] = \
            int(datetime.datetime.now().timestamp())
        request.session["saved_" + captcha_type + "_last"] = last

    @staticmethod
    def check_captcha(request, captcha_type, code):
        correct_code = request.session.get("saved_" + captcha_type + "_code")
        correct_time = request.session.get("saved_" + captcha_type + "_time")
        correct_last = request.session.get("saved_" + captcha_type + "_last")
        current_time = int(datetime.datetime.now().timestamp())
        try:
            del request.session["saved_" + captcha_type + "_code"]
            del request.session["saved_" + captcha_type + "_time"]
            del request.session["saved_" + captcha_type + "_last"]
        except KeyError:
            pass
        if None in [correct_code, correct_time, correct_last]:
            raise SessionErrors.CAPTCHA
        if current_time - correct_time > correct_last:
            raise SessionErrors.CAPTCHA_EXPIRED
        if correct_code.upper() != str(code).upper():
            raise SessionErrors.CAPTCHA
