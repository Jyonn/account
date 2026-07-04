import datetime

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


class AuthV2Flow:
    SESSION_KEY = 'auth_v2_flows'
    EXPIRE_SECONDS = 60 * 10

    @staticmethod
    def create(request, payload):
        token = get_random_string(length=24)
        flows = AuthV2Flow._load_all(request)
        flows[token] = {
            **payload,
            'captcha_passed': False,
            'code_sent': False,
            'code_verified': False,
            'created_at': int(datetime.datetime.now().timestamp()),
        }
        AuthV2Flow._save_all(request, flows)
        return token

    @staticmethod
    def get(request, token):
        flows = AuthV2Flow._load_all(request)
        flow = flows.get(token)
        if not flow:
            raise AuthV2Errors.INVALID_FLOW

        current = int(datetime.datetime.now().timestamp())
        if current - flow['created_at'] > AuthV2Flow.EXPIRE_SECONDS:
            del flows[token]
            AuthV2Flow._save_all(request, flows)
            raise AuthV2Errors.FLOW_EXPIRED

        return flow

    @staticmethod
    def update(request, token, **changes):
        flows = AuthV2Flow._load_all(request)
        flow = AuthV2Flow.get(request, token)
        flow.update(changes)
        flows[token] = flow
        AuthV2Flow._save_all(request, flows)
        return flow

    @staticmethod
    def drop(request, token):
        flows = AuthV2Flow._load_all(request)
        if token in flows:
            del flows[token]
            AuthV2Flow._save_all(request, flows)

    @staticmethod
    def _load_all(request):
        return request.session.get(AuthV2Flow.SESSION_KEY, {})

    @staticmethod
    def _save_all(request, flows):
        request.session[AuthV2Flow.SESSION_KEY] = flows
        request.session.modified = True


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

            flow_token = AuthV2Flow.create(request, dict(
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
        flow_token = AuthV2Flow.create(request, dict(
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

        flow = AuthV2Flow.update(request, flow_token, captcha_passed=True)
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
        flow = AuthV2Flow.get(request, flow_token)

        if flow['purpose'] == self.PURPOSE_LOGIN:
            if self.METHOD_PASSWORD not in flow['allowed_methods']:
                raise AuthV2Errors.METHOD_NOT_ALLOWED
            if not flow['captcha_passed']:
                raise AuthV2Errors.CAPTCHA_REQUIRED

            user = User.authenticate(flow.get('qitian'), flow.get('phone'), password)
            AuthV2Flow.drop(request, flow_token)
            return Auth.get_login_token(user)

        if not flow['code_verified']:
            raise AuthV2Errors.CODE_NOT_VERIFIED

        if flow['purpose'] == self.PURPOSE_REGISTER:
            user = User.create(flow['phone'], password)
            AuthV2Flow.drop(request, flow_token)
            return Auth.get_login_token(user)

        if flow['purpose'] == self.PURPOSE_RESET:
            user = User.get_by_phone(flow['phone'])
            user.modify_password(password)
            AuthV2Flow.drop(request, flow_token)
            return Auth.get_login_token(user)

        raise AuthV2Errors.INVALID_INTENT


class AuthV2CodeSendView(AuthV2BaseView):
    @analyse.json(
        Validator('flow_token', '流程令牌'),
        restrict_keys=False,
    )
    def post(self, request: Request):
        flow_token = self.require_flow_token(request)
        flow = AuthV2Flow.get(request, flow_token)

        if self.METHOD_CODE not in flow['allowed_methods']:
            raise AuthV2Errors.METHOD_NOT_ALLOWED
        if not flow['captcha_passed']:
            raise AuthV2Errors.CAPTCHA_REQUIRED

        send_type = {
            self.PURPOSE_LOGIN: SendMobile.LOGIN,
            self.PURPOSE_REGISTER: SendMobile.REGISTER,
            self.PURPOSE_RESET: SendMobile.FIND_PWD,
        }[flow['purpose']]
        SendMobile.send_captcha(request, flow['phone'], send_type)
        AuthV2Flow.update(request, flow_token, code_sent=True)
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
        flow = AuthV2Flow.get(request, flow_token)

        if not flow['code_sent']:
            raise AuthV2Errors.CODE_REQUIRED

        phone = SendMobile.check_captcha(request, code)
        if phone != flow['phone']:
            raise AuthV2Errors.FLOW_PHONE_MISMATCH

        if flow['purpose'] == self.PURPOSE_LOGIN:
            user = User.get_by_phone(flow['phone'])
            AuthV2Flow.drop(request, flow_token)
            return Auth.get_login_token(user)

        AuthV2Flow.update(request, flow_token, code_verified=True)
        return dict(flow_token=flow_token, next_step='password')
