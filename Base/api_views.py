from django.views import View

from Base import country
from Base.recaptcha import Recaptcha
from Base.captcha import Captcha
from Base.validator import require_get, require_json, require_post
from Base.error import Error, ERROR_DICT
from Base.response import response, error_response, Ret
from Base.send_mobile import SendMobile
from Base.session import Session


class ErrorView(View):
    @staticmethod
    def get(request):
        return response(body=ERROR_DICT)


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
                name=c['cname'] if lang_cn else c['ename'],
                flag=c['flag']
            ) for c in country.countries
        ]
        return response(body=regions)


class ReCaptchaView(View):
    RECAPTCHA = 'recaptcha'

    MODE_LOGIN_PHONE_CODE = 0
    MODE_LOGIN_PHONE_PWD = 1
    MODE_LOGIN_QTB_PWD = 2
    MODE_REGISTER = 3
    MODE_FIND_PWD = 4
    MODE_LOGIN_CODE = 5
    MODE_REGISTER_CODE = 6
    MODE_FIND_PWD_CODE = 7
    MODE_REQUIRE_CAPTCHA_LIST = [
        MODE_LOGIN_PHONE_CODE,
        MODE_LOGIN_PHONE_PWD,
        MODE_LOGIN_QTB_PWD,
        MODE_REGISTER,
        MODE_FIND_PWD
    ]
    MODE_CHECK_CODE_LIST = [
        MODE_LOGIN_CODE,
        MODE_REGISTER_CODE,
        MODE_FIND_PWD_CODE,
    ]
    MODE_LIST = [
        MODE_LOGIN_PHONE_CODE,
        MODE_LOGIN_PHONE_PWD,
        MODE_LOGIN_QTB_PWD,
        MODE_REGISTER,
        MODE_FIND_PWD,
        MODE_LOGIN_CODE,
        MODE_REGISTER_CODE,
        MODE_FIND_PWD_CODE,
    ]

    @staticmethod
    def mode_validate(mode):
        if mode not in ReCaptchaView.MODE_LIST:
            return Ret(Error.ERROR_PARAM_FORMAT)
        return Ret()

    @staticmethod
    @require_json
    @require_post(['phone'])
    def login_phone_code_handler(request):
        phone = request.d.phone

        from User.models import User
        ret = User.get_user_by_phone(phone)
        if ret.error is not Error.OK:  # 不存在
            SendMobile.send_captcha(request, phone, SendMobile.REGISTER)
            next_mode = ReCaptchaView.MODE_REGISTER_CODE
            toast_msg = '账号不存在，请注册'
        else:
            SendMobile.send_captcha(request, phone, SendMobile.LOGIN)
            next_mode = ReCaptchaView.MODE_LOGIN_CODE
            toast_msg = ''
        return response(body=dict(
            next_mode=next_mode,
            toast_msg=toast_msg,
        ))

    @staticmethod
    @require_json
    @require_post(['phone'])
    def register_handler(request):
        phone = request.d.phone

        from User.models import User
        ret = User.get_user_by_phone(phone)
        if ret.error is not Error.OK:  # 不存在
            SendMobile.send_captcha(request, phone, SendMobile.REGISTER)
            next_mode = ReCaptchaView.MODE_REGISTER_CODE
            toast_msg = ''
        else:
            SendMobile.send_captcha(request, phone, SendMobile.LOGIN)
            next_mode = ReCaptchaView.MODE_LOGIN_CODE
            toast_msg = '账号已注册，请验证'
        return response(body=dict(
            next_mode=next_mode,
            toast_msg=toast_msg,
        ))

    @staticmethod
    @require_json
    @require_post(['phone'])
    def find_pwd_handler(request):
        phone = request.d.phone
        from User.models import User
        ret = User.get_user_by_phone(phone)
        if ret.error is not Error.OK:  # 不存在
            return error_response(Error.NOT_FOUND_USER)
        SendMobile.send_captcha(request, phone, SendMobile.FIND_PWD)
        return response(body=dict(
            next_mode=ReCaptchaView.MODE_FIND_PWD_CODE,
            toast_msg='',
        ))

    @staticmethod
    @require_json
    @require_post(['phone', 'pwd'])
    def login_phone_pwd_handler(request):
        phone = request.d.phone
        pwd = request.d.pwd

        from User.models import User
        ret = User.authenticate(None, phone, pwd)
        if ret.error != Error.OK:
            return error_response(ret)
        o_user = ret.body
        if not isinstance(o_user, User):
            return error_response(Error.STRANGE)

        from User.api_views import UserView
        return response(body=UserView.get_token_info(o_user))

    @staticmethod
    @require_json
    @require_post(['qt', 'pwd'])
    def login_qt_pwd_handler(request):
        qt = request.d.qt
        pwd = request.d.pwd

        from User.models import User
        ret = User.authenticate(qt, None, pwd)
        if ret.error != Error.OK:
            return error_response(ret)
        o_user = ret.body
        if not isinstance(o_user, User):
            return error_response(Error.STRANGE)

        from User.api_views import UserView
        return response(body=UserView.get_token_info(o_user))

    @staticmethod
    @require_json
    @require_post()
    def login_code_handler(request):
        phone = request.phone

        from User.models import User
        ret = User.get_user_by_phone(phone)
        if ret.error is not Error.OK:
            return error_response(ret)

        o_user = ret.body
        if not isinstance(o_user, User):
            return error_response(Error.STRANGE)

        from User.api_views import UserView
        return response(body=UserView.get_token_info(o_user))

    @staticmethod
    @require_json
    @require_post(['pwd'])
    def register_code_handler(request):
        phone = request.phone
        pwd = request.d.pwd

        from User.models import User
        ret = User.create(phone, pwd)
        if ret.error is not Error.OK:
            return error_response(ret)
        o_user = ret.body
        if not isinstance(o_user, User):
            return error_response(Error.STRANGE)

        from User.api_views import UserView
        return response(body=UserView.get_token_info(o_user))

    @staticmethod
    @require_json
    @require_post(['pwd'])
    def find_pwd_code_handler(request):
        phone = request.phone
        pwd = request.d.pwd

        from User.models import User
        ret = User.get_user_by_phone(phone)
        if ret.error is not Error.OK:
            return error_response(ret)
        o_user = ret.body
        if not isinstance(o_user, User):
            return error_response(Error.STRANGE)

        ret = o_user.modify_password(pwd)
        if ret.error is not Error.OK:
            return error_response(ret)

        from User.api_views import UserView
        return response(body=UserView.get_token_info(o_user))

    @staticmethod
    @require_json
    @require_post([
        ('response', None, None),
        ('code', None, None),
        ('mode', mode_validate),
    ])
    def post(request):
        mode = request.d.mode

        if mode in ReCaptchaView.MODE_REQUIRE_CAPTCHA_LIST:
            resp = request.d.response
            if not resp or not Recaptcha.verify(resp):
                return error_response(Error.ERROR_PARAM_FORMAT)
        if mode in ReCaptchaView.MODE_CHECK_CODE_LIST:
            code = request.d.code
            if not code:
                return error_response(Error.ERROR_PARAM_FORMAT)
            ret = SendMobile.check_captcha(request, code)
            if ret.error is not Error.OK:
                return error_response(ret)
            request.phone = ret.body

        mode_handlers = [
            ReCaptchaView.login_phone_code_handler,
            ReCaptchaView.login_phone_pwd_handler,
            ReCaptchaView.login_qt_pwd_handler,
            ReCaptchaView.register_handler,
            ReCaptchaView.find_pwd_handler,
            ReCaptchaView.login_code_handler,
            ReCaptchaView.register_code_handler,
            ReCaptchaView.find_pwd_code_handler,
        ]

        return mode_handlers[mode](request)


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
