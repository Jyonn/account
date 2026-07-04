""" Adel Liu 180228

用户API处理函数
"""

from django.views import View
from smartdjango import analyse, Validator

from Base.auth import Auth, Request
from Base.idcard import IDCardErrors
from Base.scope import SI
from Base.qn import qn_public_manager
from User.services import UserAccountService, UserVerificationService
from User.params import UserParams


class UserView(View):
    @Auth.require_login([SI.read_base_info])
    def get(self, request: Request):
        """ GET /api/user/

        获取我的信息
        """
        return UserAccountService.get_profile(request.user, request.type)

    @analyse.json(
        UserParams.password.copy().null().default(None),
        Validator('code', '验证码')
    )
    def post(self, request: Request):
        """ POST /api/user/

        创建用户
        """
        return UserAccountService.register(request, request.json.password, request.json.code)

    @staticmethod
    @analyse.json(
        UserParams.nickname.copy().null().default(None),
        UserParams.description.copy().null().default(None),
        UserParams.qitian.copy().null().default(None),
        UserParams.birthday.copy().null().default(None),
    )
    @Auth.require_login(deny_auth_token=True)
    def put(self, request: Request):
        """ PUT /api/user/

        修改用户信息
        """
        return UserAccountService.update_profile(request.user, request.json())


class UserPhoneView(View):
    @Auth.require_login([SI.read_phone])
    def get(self, request: Request):
        """ GET /api/user/phone

        获取用户手机号
        """
        return UserAccountService.get_phone(request.user)


class UserQitianView(View):
    @analyse.query(UserParams.qitian)
    def get(self, request: Request):
        """ GET /api/user/qitian?qitian=[qitian]

        检测齐天号是否存在
        """
        return UserAccountService.ensure_qitian_exists(request.query.qitian)


class UserPhoneStatusView(View):
    @analyse.query(Validator('phone', '手机号'))
    def get(self, request: Request):
        """ GET /api/user/phone-status?phone=[phone]

        检测手机号是否已注册
        """
        return UserAccountService.get_phone_status(request.query.phone)


class TokenView(View):
    @analyse.json(UserParams.password)
    def post(self, request: Request):
        """ POST /api/user/token

        登录获取token
        """
        return UserAccountService.login_from_session(request, request.json.password)


class AvatarView(View):
    @analyse.query(Validator('filename', '文件名'))
    @Auth.require_login(deny_auth_token=True)
    def get(self, request: Request):
        """ GET /api/user/avatar

        获取七牛上传token
        """
        return UserAccountService.get_avatar_upload_token(request.user, request.query.filename)

    @staticmethod
    @analyse.json(Validator('key', '七牛存储键'), UserParams.user)
    def post(self, request: Request):
        """ POST /api/user/avatar

        七牛上传用户头像回调函数
        """
        qn_public_manager.auth_callback(self, request)

        return UserAccountService.update_avatar(request.json.user, request.json.key)


class IDCardView(View):
    @analyse.query(Validator('filename', '文件名'), UserParams.back)
    @Auth.require_login(deny_auth_token=True)
    def get(self, request: Request):
        """ GET /api/user/idcard?back=[0, 1]

        获取七牛上传token
        """
        return UserVerificationService.get_idcard_upload_token(
            user=request.user,
            filename=request.query.filename,
            back=request.query.back,
        )

    @analyse.json(Validator('key', '七牛存储键'), UserParams.user)
    @analyse.query(UserParams.back)
    def post(self, request: Request):
        """ POST /api/user/idcard?back=[0, 1]

        七牛上传用户实名认证回调函数
        """
        qn_public_manager.auth_callback(self, request)

        return UserVerificationService.update_idcard_image(
            user=request.json.user,
            key=request.json.key,
            back=request.json.back,
        )


class VerifyView(View):
    @Auth.require_login(deny_auth_token=True)
    def get(self, request: Request):
        """ GET /api/user/verify

        自动识别身份信息
        """
        return UserVerificationService.auto_verify(request.user)

    VERIFY_VALIDATORS = [
        UserParams.real_name.copy().rename('name'),
        UserParams.birthday.copy().null().default(None),
        UserParams.idcard.copy().null().default(None),
        UserParams.male.copy().null().default(None),
    ]

    @analyse.json(
        *VERIFY_VALIDATORS,
        Validator('token', '认证口令').null().default(None),
        Validator('auto', '自动认证').default(True).to(bool),
    )
    @Auth.require_login(deny_auth_token=True)
    def post(self, request: Request):
        """ POST /api/user/verify

        确认认证信息
        """
        return UserVerificationService.confirm_verify(
            user=request.user,
            payload=request.json(),
            required_keys=[validator.key for validator in VerifyView.VERIFY_VALIDATORS],
        )


class DevView(View):
    @Auth.require_login(deny_auth_token=True)
    def post(self, request: Request):
        return UserAccountService.apply_developer(request.user)
