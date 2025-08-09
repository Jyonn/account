""" Adel Liu 180228

用户API处理函数
"""
import datetime

from django.views import View
from smartdjango import analyse, Validator
from smartify import PError

from Base.auth import Auth
from Base.idcard import IDCard, IDCardErrors
from Base.mail import Email
from Base.premise_checker import PremiseCheckerErrors
from Base.scope import SI
from Base.jtoken import JWType, JWT
from Base.policy import Policy
from Base.qn import qn_public_manager, qn_res_manager
from Base.send_mobile import SendMobile
from Base.session import Session, SessionErrors

from User.models import User
from User.params import UserParams


class UserView(View):
    @Auth.require_login([SI.read_base_info])
    def get(self, request):
        """ GET /api/user/

        获取我的信息
        """
        user = request.user
        return user.d_oauth() if request.type_ == JWType.AUTH_TOKEN else user.d()

    @analyse.json(UserParams.password, Validator('code', '验证码'))
    def post(self, request):
        """ POST /api/user/

        创建用户
        """
        code = request.json.code
        password = request.json.password

        phone = SendMobile.check_captcha(request, code)

        user = User.create(phone, password)
        return Auth.get_login_token(user)

    @staticmethod
    @analyse.json(
        UserParams.nickname.copy().null(),
        UserParams.description.copy().null(),
        UserParams.qitian.copy().null(),
        UserParams.birthday.copy().null(),
    )
    @Auth.require_login(deny_auth_token=True)
    def put(self, request):
        """ PUT /api/user/

        修改用户信息
        """
        user = request.user

        user.modify_info(**request.json())
        return user.d()


class UserPhoneView(View):
    @Auth.require_login([SI.read_phone])
    def get(self, request):
        """ GET /api/user/phone

        获取用户手机号
        """
        return request.user.phone


class TokenView(View):
    @analyse.json(UserParams.password)
    def post(self, request):
        """ POST /api/user/token

        登录获取token
        """
        password = request.json.password
        login_type = Session.load(request, SendMobile.LOGIN_TYPE, once_delete=False)
        if not login_type:
            raise SessionErrors.SESSION
        login_value = Session.load(request, login_type, once_delete=False)
        if not login_value:
            raise SessionErrors.SESSION
        if login_type == SendMobile.PHONE_NUMBER:
            user = User.authenticate(None, login_value, password)
        else:
            user = User.authenticate(login_value, None, password)
        return Auth.get_login_token(user)


class AvatarView(View):
    @analyse.query(Validator('filename', '文件名'))
    @Auth.require_login(deny_auth_token=True)
    def get(self, request):
        """ GET /api/user/avatar

        获取七牛上传token
        """
        user = request.user
        filename = request.query.filename

        crt_time = datetime.datetime.now().timestamp()
        key = 'user/%s/avatar/%s/%s' % (user.user_str_id, crt_time, filename)
        qn_token, key = qn_public_manager.get_upload_token(key, Policy.avatar(user.user_str_id))
        return dict(upload_token=qn_token, key=key)

    @staticmethod
    @analyse.json(Validator('key', '七牛存储键'), UserParams.user)
    def post(self, request):
        """ POST /api/user/avatar

        七牛上传用户头像回调函数
        """
        qn_public_manager.auth_callback(self, request)

        key = request.json.key
        user = request.json.user
        user.modify_avatar(key)
        return user.d()


class IDCardView(View):
    @analyse.query(Validator('filename', '文件名'), UserParams.back)
    @Auth.require_login(deny_auth_token=True)
    def get(self, request):
        """ GET /api/user/idcard?back=[0, 1]

        获取七牛上传token
        """
        user = request.user
        filename = request.query.filename
        back = request.query.back

        if user.verify_status != User.VERIFY_STATUS_UNVERIFIED:
            if user.verify_status == User.VERIFY_STATUS_UNDER_AUTO or \
                    user.verify_status == User.VERIFY_STATUS_UNDER_MANUAL:
                raise IDCardErrors.VERIFYING('无法重新上传')
            else:
                raise IDCardErrors.REAL_VERIFIED('无法重新上传')

        crt_time = datetime.datetime.now().timestamp()
        key = 'user/%s/card/%s/%s/%s' % (user.user_str_id,
                                         ['front', 'back'][back], crt_time, filename)
        policy = Policy.verify_back if back else Policy.verify_front
        qn_token, key = qn_res_manager.get_upload_token(key, policy(user.user_str_id))
        return dict(upload_token=qn_token, key=key)

    @analyse.json(Validator('key', '七牛存储键'), UserParams.user)
    @analyse.query(UserParams.back)
    def post(self, request):
        """ POST /api/user/idcard?back=[0, 1]

        七牛上传用户实名认证回调函数
        """
        qn_public_manager.auth_callback(self, request)

        key = request.json.key
        back = request.json.back
        user = request.json.user

        if user.verify_status != User.VERIFY_STATUS_UNVERIFIED:
            if user.verify_status == User.VERIFY_STATUS_UNDER_AUTO or \
                    user.verify_status == User.VERIFY_STATUS_UNDER_MANUAL:
                raise IDCardErrors.VERIFYING('无法重新上传')
            else:
                raise IDCardErrors.REAL_VERIFIED('无法重新上传')

        if back:
            return user.upload_verify_back(key)
        else:
            return user.upload_verify_front(key)


class VerifyView(View):
    @Auth.require_login(deny_auth_token=True)
    def get(self, request):
        """ GET /api/user/verify

        自动识别身份信息
        """
        user = request.user

        if user.verify_status != User.VERIFY_STATUS_UNVERIFIED:
            if user.verify_status == User.VERIFY_STATUS_UNDER_AUTO or \
                    user.verify_status == User.VERIFY_STATUS_UNDER_MANUAL:
                raise IDCardErrors.VERIFYING('无法继续识别')
            else:
                raise IDCardErrors.REAL_VERIFIED('无法继续识别')

        urls = user.get_card_urls()
        if not urls['front'] or not urls['back']:
            raise IDCardErrors.CARD_NOT_COMPLETE

        front_info = IDCard.detect_front(urls['front'])
        back_info = IDCard.detect_back(urls['back'])

        back_info.update(front_info)
        back_info['type'] = 'idcard-verify'
        back_info['user_id'] = user.user_str_id
        token, verify_info = JWT.encrypt(back_info, expire_second=60 * 5)
        verify_info['token'] = token
        user.update_verify_type(User.VERIFY_CHINA)
        return verify_info

    VERIFY_PARAMS = [
        UserParams.real_name.copy().rename('name'),
        UserParams.birthday.copy().null(),
        UserParams.idcard.copy().null(),
        UserParams.male.copy().null(),
    ]

    @analyse.json(
        *VERIFY_PARAMS,
        Validator('token', '认证口令').null(),
        Validator('auto', '自动认证').default(True).to(bool),
    )
    @Auth.require_login(deny_auth_token=True)
    def post(self, request):
        """ POST /api/user/verify

        确认认证信息
        """
        user = request.user

        if user.verify_status != User.VERIFY_STATUS_UNVERIFIED:
            if user.verify_status == User.VERIFY_STATUS_UNDER_AUTO or \
                    user.verify_status == User.VERIFY_STATUS_UNDER_MANUAL:
                raise IDCardErrors.VERIFYING('无法继续确认')
            else:
                raise IDCardErrors.REAL_VERIFIED('无法继续确认')

        if request.json.auto:
            # 自动验证
            token = request.json.token
            dict_ = JWT.decrypt(token)
            if 'user_id' not in dict_:
                raise IDCardErrors.AUTO_VERIFY_FAILED
            if user.user_str_id != dict_['user_id']:
                raise IDCardErrors.AUTO_VERIFY_FAILED

            crt_time = datetime.datetime.now().timestamp()
            valid_start = datetime.datetime.strptime(dict_['valid_start'], '%Y-%m-%d').timestamp()
            valid_end = datetime.datetime.strptime(dict_['valid_end'], '%Y-%m-%d').timestamp()
            if valid_start > crt_time or crt_time > valid_end:
                raise IDCardErrors.CARD_VALID_EXPIRED

            user.update_card_info(
                dict_['name'],
                dict_['male'],
                dict_['idcard'],
                datetime.datetime.strptime(dict_['birthday'], '%Y-%m-%d').date(),
            )
            user.update_verify_status(User.VERIFY_STATUS_DONE)
        else:
            # 人工验证
            for param in VerifyView.VERIFY_PARAMS:
                if not request.json[param.name]:
                    return PError.NULL_NOT_ALLOW(param.name, param.read_name)

            user.update_card_info(
                name=request.json.name,
                birthday=request.json.birthday,
                idcard=request.json.idcard,
                male=request.json.male,
            )
            user.update_verify_status(User.VERIFY_STATUS_UNDER_MANUAL)
            Email.real_verify(user, '')
        return user.d()


class DevView(View):
    @Auth.require_login(deny_auth_token=True)
    def post(self, request):
        user = request.user
        if user.verify_status != User.VERIFY_STATUS_DONE:
            return PremiseCheckerErrors.REQUIRE_REAL_VERIFY
        user.developer()
        return user.d()


# def set_unique_user_str_id(_):
#     for user in User.objects.all():
#         user.user_str_id = User.get_unique_id()
#         user.save()
