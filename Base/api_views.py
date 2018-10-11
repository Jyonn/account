from django.views import View

from Base import country
from Base.captcha import Captcha, GT
from Base.common import deprint
from Base.validator import require_get, require_json, require_post
from Base.error import Error
from Base.response import response, error_response
from Base.send_mobile import SendMobile
from Base.session import Session


class ErrorView(View):
    @staticmethod
    def get(request):
        return response(body=Error.get_error_dict())


class RegionView(View):
    @staticmethod
    def process_lang(lang):
        if lang not in ['cn', 'en']:
            return 'cn'
        return lang

    @staticmethod
    @require_get([{
        'value': 'lang',
        'default': True,
        'default_value': 'cn',
        'process': process_lang,
    }])
    def get(request):
        lang = request.d.lang
        lang_cn = lang == country.LANG_CN
        regions = [
            dict(
                num=c['num'],
                name=c['cname'] if lang_cn else c['ename']
            ) for c in country.countries
        ]
        return response(body=regions)


class CaptchaView(View):
    # @staticmethod
    # @require_get()
    # def get(request):
    #     return response(body=Captcha.get(request))

    @staticmethod
    @require_json
    @require_post(['challenge', 'validate', 'seccode', 'account',
                   {"value": 'type', "process": int}])
    def post(request):
        challenge = request.d.challenge
        validate = request.d.validate
        seccode = request.d.seccode
        account = request.d.account
        type_ = request.d.type
        # deprint(Session.load(request, GT.GT_STATUS_SESSION_KEY), challenge, validate, seccode)
        if not Captcha.verify(request, challenge, validate, seccode):
            return error_response(Error.ERROR_INTERACTION)

        from User.models import User
        if type_ == -1:
            # 手机号登录
            ret = User.get_user_by_phone(account)
            if ret.error is not Error.OK:
                return error_response(ret)
            Session.save(request, SendMobile.PHONE_NUMBER, account, visit_time=5)
            Session.save(request, SendMobile.LOGIN_TYPE, SendMobile.PHONE_NUMBER, visit_time=5)
        elif type_ == -2:
            # 齐天号登录
            ret = User.get_user_by_qitian(account)
            if ret.error is not Error.OK:
                return error_response(ret)
            Session.save(request, SendMobile.QITIAN_ID, account, visit_time=5)
            Session.save(request, SendMobile.LOGIN_TYPE, SendMobile.QITIAN_ID, visit_time=5)
        else:
            # 手机号注册
            ret = User.get_user_by_phone(account)
            if ret.error is Error.OK:
                return error_response(Error.PHONE_EXIST)
            SendMobile.send_captcha(request, account, type_)
        return response()
