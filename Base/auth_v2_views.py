import datetime
import hashlib

from django.core import signing
from django.utils.crypto import get_random_string
from django.views import View
from smartdjango import Error, Code, Validator, analyse

from Base.auth import Auth, Request
from Base.recaptcha import Recaptcha
from Base.send_mobile import SendMobile
from User.models import User
from User.params import UserParams
from User.validators import UserErrors


@Error.register
class AuthV2Errors:
    FORMAT = Error('格式错误', code=Code.BadRequest)
    INVALID_FLOW = Error('登录流程无效，请重新开始', code=Code.BadRequest)
    FLOW_EXPIRED = Error('登录流程已过期，请重新开始', code=Code.BadRequest)
    CAPTCHA_REQUIRED = Error('请先完成人机验证', code=Code.BadRequest)
    CODE_REQUIRED = Error('请先发送验证码', code=Code.BadRequest)
    CODE_NOT_VERIFIED = Error('请先完成验证码校验', code=Code.BadRequest)
    INVALID_INTENT = Error('不支持的登录流程', code=Code.BadRequest)
    INVALID_IDENTITY_TYPE = Error('不支持的身份类型', code=Code.BadRequest)
    METHOD_NOT_ALLOWED = Error('当前流程不支持此方式', code=Code.BadRequest)
    PHONE_REQUIRED = Error('请输入手机号', code=Code.BadRequest)
    QITIAN_REQUIRED = Error('请输入齐天号', code=Code.BadRequest)
    FLOW_PHONE_MISMATCH = Error('验证码手机号不匹配，请重新开始', code=Code.BadRequest)
    RECOVER_PHONE_ONLY = Error('找回密码仅支持手机号', code=Code.BadRequest)
    CODE_INVALID = Error('验证失败', code=Code.BadRequest)
    CODE_EXPIRED = Error('验证码过期，请重试', code=Code.BadRequest)


class AuthV2Flow:
    SALT = 'auth-v2-flow'
    EXPIRE_SECONDS = 60 * 10

    @staticmethod
    def create(payload):
        return AuthV2Flow._dump({
            **payload,
            'captcha_passed': False,
            'code_sent': False,
            'code_verified': False,
            'created_at': int(datetime.datetime.now().timestamp()),
        })

    @staticmethod
    def get(token):
        try:
            return signing.loads(token, salt=AuthV2Flow.SALT, max_age=AuthV2Flow.EXPIRE_SECONDS)
        except signing.SignatureExpired:
            raise AuthV2Errors.FLOW_EXPIRED
        except signing.BadSignature:
            raise AuthV2Errors.INVALID_FLOW

    @staticmethod
    def update(token, **changes):
        flow = AuthV2Flow.get(token)
        flow.update(changes)
        return AuthV2Flow._dump(flow)

    @staticmethod
    def issue_code(token, phone):
        code = get_random_string(length=6, allowed_chars='1234567890')
        SendMobile._send_sms(phone, code)
        return AuthV2Flow.update(
            token,
            code_sent=True,
            code_verified=False,
            code_digest=AuthV2Flow._build_code_digest(phone, code),
            code_created_at=int(datetime.datetime.now().timestamp()),
        )

    @staticmethod
    def verify_code(flow, code):
        current_time = int(datetime.datetime.now().timestamp())
        code_created_at = flow.get('code_created_at')
        code_digest = flow.get('code_digest')
        if not code_created_at or not code_digest:
            raise AuthV2Errors.CODE_INVALID
        if current_time - code_created_at > SendMobile.CAPTCHA_EXPIRE_MINUTES * 60:
            raise AuthV2Errors.CODE_EXPIRED
        if code_digest != AuthV2Flow._build_code_digest(flow.get('phone'), code):
            raise AuthV2Errors.CODE_INVALID

    @staticmethod
    def _build_code_digest(phone, code):
        return hashlib.sha256(f'{AuthV2Flow.SALT}:{phone}:{code}'.encode('utf-8')).hexdigest()

    @staticmethod
    def _dump(payload):
        return signing.dumps(payload, salt=AuthV2Flow.SALT, compress=True)


class AuthV2BaseView(View):
    IDENTITY_PHONE = 'phone'
    IDENTITY_QITIAN = 'qitian'
    INTENT_LOGIN = 'login'
    INTENT_RECOVER = 'recover'
    PURPOSE_LOGIN = 'login'
    PURPOSE_REGISTER = 'register'
    PURPOSE_RESET = 'reset'
    METHOD_PASSWORD = 'password'
    METHOD_CODE = 'code'

    @staticmethod
    def resolve_phone_registered(phone):
        try:
            User.get_by_phone(phone)
            return True
        except Error as e:
            if not e.equals(UserErrors.USER_NOT_FOUND):
                raise e
            return False

    @staticmethod
    def require_flow_token(request: Request):
        flow_token = request.json.flow_token
        if not flow_token:
            raise AuthV2Errors.INVALID_FLOW
        return flow_token


class AuthV2SessionView(AuthV2BaseView):
    @analyse.json(
        Validator('identity_type', '身份类型'),
        Validator('intent', '登录意图').default(AuthV2BaseView.INTENT_LOGIN),
        Validator('phone', '手机号').null().default(None),
        Validator('qt', '齐天号').null().default(None),
        restrict_keys=False,
    )
    def post(self, request: Request):
        identity_type = request.json.identity_type
        intent = request.json.intent

        if identity_type not in [self.IDENTITY_PHONE, self.IDENTITY_QITIAN]:
            raise AuthV2Errors.INVALID_IDENTITY_TYPE
        if intent not in [self.INTENT_LOGIN, self.INTENT_RECOVER]:
            raise AuthV2Errors.INVALID_INTENT

        if identity_type == self.IDENTITY_PHONE:
            phone = request.json.phone
            if not phone:
                raise AuthV2Errors.PHONE_REQUIRED

            if intent == self.INTENT_RECOVER:
                User.get_by_phone(phone)
                purpose = self.PURPOSE_RESET
                user_state = 'existing'
                allowed_methods = [self.METHOD_CODE]
            else:
                registered = self.resolve_phone_registered(phone)
                purpose = self.PURPOSE_LOGIN if registered else self.PURPOSE_REGISTER
                user_state = 'existing' if registered else 'new'
                allowed_methods = [self.METHOD_PASSWORD, self.METHOD_CODE] if registered else [self.METHOD_CODE]

            flow_token = AuthV2Flow.create(dict(
                identity_type=identity_type,
                identity_value=phone,
                phone=phone,
                qitian=None,
                purpose=purpose,
                user_state=user_state,
                allowed_methods=allowed_methods,
            ))

            return dict(
                flow_token=flow_token,
                identity_type=identity_type,
                user_state=user_state,
                purpose=purpose,
                allowed_methods=allowed_methods,
            )

        if intent == self.INTENT_RECOVER:
            raise AuthV2Errors.RECOVER_PHONE_ONLY

        qitian = request.json.qt
        if not qitian:
            raise AuthV2Errors.QITIAN_REQUIRED

        User.get_by_qitian(qitian)
        flow_token = AuthV2Flow.create(dict(
            identity_type=identity_type,
            identity_value=qitian,
            phone=None,
            qitian=qitian,
            purpose=self.PURPOSE_LOGIN,
            user_state='existing',
            allowed_methods=[self.METHOD_PASSWORD],
        ))
        return dict(
            flow_token=flow_token,
            identity_type=identity_type,
            user_state='existing',
            purpose=self.PURPOSE_LOGIN,
            allowed_methods=[self.METHOD_PASSWORD],
        )


class AuthV2CaptchaView(AuthV2BaseView):
    @analyse.json(
        Validator('flow_token', '流程令牌'),
        Validator('response', '人机验证码').null().default(None),
        restrict_keys=False,
    )
    def post(self, request: Request):
        flow_token = self.require_flow_token(request)
        response = request.json.response

        if not response or not Recaptcha.verify(response):
            raise AuthV2Errors.FORMAT(details='人机验证失败')

        flow_token = AuthV2Flow.update(flow_token, captcha_passed=True)
        flow = AuthV2Flow.get(flow_token)
        return dict(
            flow_token=flow_token,
            purpose=flow['purpose'],
            allowed_methods=flow['allowed_methods'],
        )


class AuthV2PasswordView(AuthV2BaseView):
    @analyse.json(
        Validator('flow_token', '流程令牌'),
        UserParams.password.copy().rename('password'),
        restrict_keys=False,
    )
    def post(self, request: Request):
        flow_token = self.require_flow_token(request)
        password = request.json.password
        flow = AuthV2Flow.get(flow_token)

        if flow['purpose'] == self.PURPOSE_LOGIN:
            if self.METHOD_PASSWORD not in flow['allowed_methods']:
                raise AuthV2Errors.METHOD_NOT_ALLOWED
            if not flow['captcha_passed']:
                raise AuthV2Errors.CAPTCHA_REQUIRED

            user = User.authenticate(flow.get('qitian'), flow.get('phone'), password)
            return Auth.get_login_token(user)

        if not flow['code_verified']:
            raise AuthV2Errors.CODE_NOT_VERIFIED

        if flow['purpose'] == self.PURPOSE_REGISTER:
            user = User.create(flow['phone'], password)
            return Auth.get_login_token(user)

        if flow['purpose'] == self.PURPOSE_RESET:
            user = User.get_by_phone(flow['phone'])
            user.modify_password(password)
            return Auth.get_login_token(user)

        raise AuthV2Errors.INVALID_INTENT


class AuthV2CodeSendView(AuthV2BaseView):
    @analyse.json(
        Validator('flow_token', '流程令牌'),
        restrict_keys=False,
    )
    def post(self, request: Request):
        flow_token = self.require_flow_token(request)
        flow = AuthV2Flow.get(flow_token)

        if self.METHOD_CODE not in flow['allowed_methods']:
            raise AuthV2Errors.METHOD_NOT_ALLOWED
        if not flow['captcha_passed']:
            raise AuthV2Errors.CAPTCHA_REQUIRED

        flow_token = AuthV2Flow.issue_code(flow_token, flow['phone'])
        return dict(flow_token=flow_token, sent=True)


class AuthV2CodeVerifyView(AuthV2BaseView):
    @analyse.json(
        Validator('flow_token', '流程令牌'),
        Validator('code', '验证码'),
        restrict_keys=False,
    )
    def post(self, request: Request):
        flow_token = self.require_flow_token(request)
        code = request.json.code
        flow = AuthV2Flow.get(flow_token)

        if not flow['code_sent']:
            raise AuthV2Errors.CODE_REQUIRED

        AuthV2Flow.verify_code(flow, code)

        if flow['purpose'] == self.PURPOSE_LOGIN:
            user = User.get_by_phone(flow['phone'])
            return Auth.get_login_token(user)

        flow_token = AuthV2Flow.update(
            flow_token,
            code_verified=True,
        )
        return dict(flow_token=flow_token, next_step='password')
