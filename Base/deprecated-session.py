# 171203 Adel Liu
# 暂时弃用，图片验证码可以继续使用

import datetime

from Base.common import deprint


def save_session(request, key, value):
    request.session["saved_" + key] = value


def load_session(request, key, once_delete=True):
    value = request.session.get("saved_" + key)
    if value is None:
        return None
    if once_delete:
        del request.session["saved_" + key]
    return value


def save_captcha(request, captcha_type, code, last=300):
    request.session["saved_" + captcha_type + "_code"] = str(code)
    request.session["saved_" + captcha_type + "_time"] = int(datetime.datetime.now().timestamp())
    request.session["saved_" + captcha_type + "_last"] = last
    return None


def check_captcha(request, captcha_type, code):
    correct_code = request.session.get("saved_" + captcha_type + "_code")
    correct_time = request.session.get("saved_" + captcha_type + "_time")
    correct_last = request.session.get("saved_" + captcha_type + "_last")
    current_time = int(datetime.datetime.now().timestamp())
    # print(correct_time, correct_last, correct_code, current_time)
    try:
        del request.session["saved_" + captcha_type + "_code"]
        del request.session["saved_" + captcha_type + "_time"]
        del request.session["saved_" + captcha_type + "_last"]
    except KeyError as err:
        deprint(str(err))
    if None in [correct_code, correct_time, correct_last]:
        return False
    if current_time - correct_time > correct_last:
        return False
    return correct_code.upper() == str(code).upper()
