from django.views import View
from smartdjango import Validator, analyse, Error, Code

from Base import country
from Base.auth import Auth
from Base.recaptcha import Recaptcha
from Base.send_mobile import SendMobile
from User.models import User

PM_PHONE = Validator('phone', '手机号')
PM_PWD = Validator('pwd', '密码')


@Error.register
class BaseErrors:
    FORMAT = Error("格式错误", code=Code.BadRequest)


def process_lang(lang):
    """format language"""
    if lang not in ['cn', 'en']:
        return 'cn'
    return lang


class Region(View):
    @analyse.query(Validator('lang', '语言').default('cn').to(process_lang))
    def get(self, request):
        lang = request.query.lang
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

    @analyse.body(PM_PHONE)
    def login_phone_code_handler(self, request):
        phone = request.body.phone

        try:
            User.get_by_phone(phone)
            SendMobile.send_captcha(request, phone, SendMobile.LOGIN)
            next_mode = ReCaptchaView.MODE_LOGIN_CODE
            toast_msg = ''
        except Error:
            SendMobile.send_captcha(request, phone, SendMobile.REGISTER)
            next_mode = ReCaptchaView.MODE_REGISTER_CODE
            toast_msg = '账号不存在，请注册'

        return dict(
            next_mode=next_mode,
            toast_msg=toast_msg,
        )

    @analyse.body(PM_PHONE)
    def register_handler(self, request):
        phone = request.body.phone

        try:
            User.get_by_phone(phone)
            SendMobile.send_captcha(request, phone, SendMobile.LOGIN)
            next_mode = ReCaptchaView.MODE_LOGIN_CODE
            toast_msg = '账号已注册，请验证'
        except Error:
            SendMobile.send_captcha(request, phone, SendMobile.REGISTER)
            next_mode = ReCaptchaView.MODE_REGISTER_CODE
            toast_msg = ''

        return dict(
            next_mode=next_mode,
            toast_msg=toast_msg,
        )

    @analyse.body(PM_PHONE)
    def find_pwd_handler(self, request):
        phone = request.body.phone
        User.get_by_phone(phone)
        SendMobile.send_captcha(request, phone, SendMobile.FIND_PWD)
        return dict(
            next_mode=ReCaptchaView.MODE_FIND_PWD_CODE,
            toast_msg='',
        )

    @analyse.body(PM_PHONE, PM_PWD)
    def login_phone_pwd_handler(self, request):
        phone = request.body.phone
        pwd = request.body.pwd

        user = User.authenticate(None, phone, pwd)
        return Auth.get_login_token(user)

    @analyse.body(Validator('qt', '齐天号'), PM_PWD)
    def login_qt_pwd_handler(self, request):
        qt = request.body.qt
        pwd = request.body.pwd

        user = User.authenticate(qt, None, pwd)

        return Auth.get_login_token(user)

    def login_code_handler(self, request):
        phone = request.phone
        user = User.get_by_phone(phone)

        return Auth.get_login_token(user)

    @analyse.body(PM_PWD)
    def register_code_handler(self, request):
        phone = request.phone
        pwd = request.body.pwd
        user = User.create(phone, pwd)

        return Auth.get_login_token(user)

    @analyse.body(PM_PWD)
    def find_pwd_code_handler(self, request):
        phone = request.phone
        pwd = request.body.pwd

        user = User.get_by_phone(phone)
        user.modify_password(pwd)

        return Auth.get_login_token(user)

    @analyse.body(
        Validator('response', '人机验证码').null(),
        Validator('code', '短信验证码').null(),
        Validator('mode', '登录模式').bool(lambda x: x in ReCaptchaView.MODE_LIST),
        restrict_keys=False,
    )
    def post(self, request):
        mode = request.body.mode

        if mode in ReCaptchaView.MODE_REQUIRE_CAPTCHA_LIST:
            resp = request.body.response
            if not resp or not Recaptcha.verify(resp):
                raise BaseErrors.FORMAT(details='人机验证失败')
        if mode in ReCaptchaView.MODE_CHECK_CODE_LIST:
            code = request.body.code
            if not code:
                raise BaseErrors.FORMAT(details='验证码不能为空')
            request.phone = SendMobile.check_captcha(request, code)

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

        return mode_handlers[mode](self, request)
