from SmartDjango import Analyse, P, BaseError, E
from SmartDjango.models.base import ModelError
from django.views import View

from Base import country
from Base.auth import Auth
from Base.recaptcha import Recaptcha
from Base.send_mobile import SendMobile
from Base.session import Session
from User.api_views import UserView
from User.models import UserError, User

PM_PHONE = P('phone', '手机号')
PM_PWD = P('pwd', '密码')


class ErrorView(View):
    @staticmethod
    def get(r):
        return E.all()


def process_lang(lang):
    """format language"""
    if lang not in ['cn', 'en']:
        return 'cn'
    return lang


class RegionView(View):
    @staticmethod
    @Analyse.r(q=[P('lang', '语言').default('cn').process(process_lang)])
    def get(r):
        lang = r.d.lang
        lang_cn = lang == country.LANG_CN
        regions = [
            dict(
                num=c['num'],
                name=c['cname'] if lang_cn else c['ename'],
                flag=c['flag'],
                detail=c.get('detail'),
            ) for c in country.countries
        ]
        return regions


def mode_validate(mode):
    if mode not in ReCaptchaView.MODE_LIST:
        raise ModelError.FIELD_FORMAT


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
    @Analyse.r([PM_PHONE])
    def login_phone_code_handler(r):
        phone = r.d.phone

        try:
            User.get_by_phone(phone)
            SendMobile.send_captcha(r, phone, SendMobile.LOGIN)
            next_mode = ReCaptchaView.MODE_LOGIN_CODE
            toast_msg = ''
        except E:
            SendMobile.send_captcha(r, phone, SendMobile.REGISTER)
            next_mode = ReCaptchaView.MODE_REGISTER_CODE
            toast_msg = '账号不存在，请注册'

        return dict(
            next_mode=next_mode,
            toast_msg=toast_msg,
        )

    @staticmethod
    @Analyse.r([PM_PHONE])
    def register_handler(r):
        phone = r.d.phone

        try:
            User.get_by_phone(phone)
            SendMobile.send_captcha(r, phone, SendMobile.LOGIN)
            next_mode = ReCaptchaView.MODE_LOGIN_CODE
            toast_msg = '账号已注册，请验证'
        except E:
            SendMobile.send_captcha(r, phone, SendMobile.REGISTER)
            next_mode = ReCaptchaView.MODE_REGISTER_CODE
            toast_msg = ''

        return dict(
            next_mode=next_mode,
            toast_msg=toast_msg,
        )

    @staticmethod
    @Analyse.r([PM_PHONE])
    def find_pwd_handler(r):
        phone = r.d.phone
        User.get_by_phone(phone)
        SendMobile.send_captcha(r, phone, SendMobile.FIND_PWD)
        return dict(
            next_mode=ReCaptchaView.MODE_FIND_PWD_CODE,
            toast_msg='',
        )

    @staticmethod
    @Analyse.r([PM_PHONE, PM_PWD])
    def login_phone_pwd_handler(r):
        phone = r.d.phone
        pwd = r.d.pwd

        user = User.authenticate(None, phone, pwd)
        return Auth.get_login_token(user)

    @staticmethod
    @Analyse.r([P('qt', '齐天号'), PM_PWD])
    def login_qt_pwd_handler(r):
        qt = r.d.qt
        pwd = r.d.pwd

        user = User.authenticate(qt, None, pwd)

        return Auth.get_login_token(user)

    @staticmethod
    @Analyse.r()
    def login_code_handler(r):
        phone = r.phone
        user = User.get_by_phone(phone)

        return Auth.get_login_token(user)

    @staticmethod
    @Analyse.r([PM_PWD])
    def register_code_handler(r):
        phone = r.phone
        pwd = r.d.pwd
        user = User.create(phone, pwd)

        return Auth.get_login_token(user)

    @staticmethod
    @Analyse.r([PM_PWD])
    def find_pwd_code_handler(r):
        phone = r.phone
        pwd = r.d.pwd

        user = User.get_by_phone(phone)
        user.modify_password(pwd)

        return Auth.get_login_token(user)

    @staticmethod
    @Analyse.r([
        P('response', '人机验证码').null(),
        P('code', '短信验证码').null(),
        P('mode', '登录模式').validate(mode_validate),
    ])
    def post(r):
        mode = r.d.mode

        if mode in ReCaptchaView.MODE_REQUIRE_CAPTCHA_LIST:
            resp = r.d.response
            if not resp or not Recaptcha.verify(resp):
                return BaseError.FIELD_FORMAT('人机验证失败')
        if mode in ReCaptchaView.MODE_CHECK_CODE_LIST:
            code = r.d.code
            if not code:
                return BaseError.FIELD_FORMAT
            r.phone = SendMobile.check_captcha(r, code)

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

        return mode_handlers[mode](r)
