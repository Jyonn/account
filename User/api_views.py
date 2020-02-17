""" Adel Liu 180228

用户API处理函数
"""
import datetime

from SmartDjango import P, Analyse
from django.views import View
from smartify import PError

from Base.auth import Auth
from Base.idcard import IDCard, IDCardError
from Base.mail import Email
from Base.premise_checker import PremiseCheckerError
from Base.scope import SI
from Base.jtoken import JWType, JWT
from Base.policy import Policy
from Base.qn import qn_public_manager, qn_res_manager
from Base.send_mobile import SendMobile
from Base.session import Session, SessionError

from User.models import User, UserP


class UserView(View):
    @staticmethod
    @Auth.require_login([SI.read_base_info])
    def get(r):
        """ GET /api/user/

        获取我的信息
        """
        user = r.user
        return user.d_oauth() if r.type_ == JWType.AUTH_TOKEN else user.d()

    @staticmethod
    @Analyse.r([UserP.password, P('code', '验证码')])
    def post(r):
        """ POST /api/user/

        创建用户
        """
        code = r.d.code
        password = r.d.password

        phone = SendMobile.check_captcha(r, code)

        user = User.create(phone, password)
        return Auth.get_login_token(user)

    @staticmethod
    @Analyse.r(
        [
            UserP.nickname.clone().null(),
            UserP.description.clone().null(),
            UserP.qitian.clone().null(),
            UserP.birthday.clone().null(),
        ]
    )
    @Auth.require_login(deny_auth_token=True)
    def put(r):
        """ PUT /api/user/

        修改用户信息
        """
        user = r.user

        user.modify_info(**r.d.dict())
        return user.d()


class UserPhoneView(View):
    @staticmethod
    @Auth.require_login([SI.read_phone])
    def get(r):
        """ GET /api/user/phone

        获取用户手机号
        """
        return r.user.phone


class TokenView(View):
    @staticmethod
    @Analyse.r([UserP.password])
    def post(r):
        """ POST /api/user/token

        登录获取token
        """
        password = r.d.password
        login_type = Session.load(r, SendMobile.LOGIN_TYPE, once_delete=False)
        if not login_type:
            raise SessionError.SESSION
        login_value = Session.load(r, login_type, once_delete=False)
        if not login_value:
            raise SessionError.SESSION
        if login_type == SendMobile.PHONE_NUMBER:
            user = User.authenticate(None, login_value, password)
        else:
            user = User.authenticate(login_value, None, password)
        return Auth.get_login_token(user)


class AvatarView(View):
    @staticmethod
    @Analyse.r(q=[P('filename', '文件名')])
    @Auth.require_login(deny_auth_token=True)
    def get(r):
        """ GET /api/user/avatar

        获取七牛上传token
        """
        user = r.user
        filename = r.d.filename

        import datetime
        crt_time = datetime.datetime.now().timestamp()
        key = 'user/%s/avatar/%s/%s' % (user.user_str_id, crt_time, filename)
        qn_token, key = qn_public_manager.get_upload_token(key, Policy.avatar(user.user_str_id))
        return dict(upload_token=qn_token, key=key)

    @staticmethod
    @Analyse.r([P('key', '七牛存储键'), UserP.user])
    def post(r):
        """ POST /api/user/avatar

        七牛上传用户头像回调函数
        """
        qn_public_manager.qiniu_auth_callback(r)

        key = r.d.key
        user = r.d.user
        user.modify_avatar(key)
        return user.d()


class IDCardView(View):
    @staticmethod
    @Analyse.r(q=[P('filename', '文件名'), UserP.back])
    @Auth.require_login(deny_auth_token=True)
    def get(r):
        """ GET /api/user/idcard?back=[0, 1]

        获取七牛上传token
        """
        user = r.user
        filename = r.d.filename
        back = int(bool(r.d.back))

        if user.verify_status != User.VERIFY_STATUS_UNVERIFIED:
            if user.verify_status == User.VERIFY_STATUS_UNDER_AUTO or \
                    user.verify_status == User.VERIFY_STATUS_UNDER_MANUAL:
                raise IDCardError.VERIFYING('无法重新上传')
            else:
                raise IDCardError.REAL_VERIFIED('无法重新上传')

        import datetime
        crt_time = datetime.datetime.now().timestamp()
        key = 'user/%s/card/%s/%s/%s' % (user.user_str_id,
                                         ['front', 'back'][back], crt_time, filename)
        policy = Policy.verify_back if back else Policy.verify_front
        qn_token, key = qn_res_manager.get_upload_token(key, policy(user.user_str_id))
        return dict(upload_token=qn_token, key=key)

    @staticmethod
    @Analyse.r(b=[P('key', '七牛存储键'), UserP.user], q=[UserP.back])
    def post(r):
        """ POST /api/user/idcard?back=[0, 1]

        七牛上传用户实名认证回调函数
        """
        qn_public_manager.qiniu_auth_callback(r)

        key = r.d.key
        back = r.d.back
        user = r.d.user

        if user.verify_status != User.VERIFY_STATUS_UNVERIFIED:
            if user.verify_status == User.VERIFY_STATUS_UNDER_AUTO or \
                    user.verify_status == User.VERIFY_STATUS_UNDER_MANUAL:
                raise IDCardError.VERIFYING('无法重新上传')
            else:
                raise IDCardError.REAL_VERIFIED('无法重新上传')

        if back:
            return user.upload_verify_back(key)
        else:
            return user.upload_verify_front(key)


class VerifyView(View):
    @staticmethod
    @Auth.require_login(deny_auth_token=True)
    def get(r):
        """ GET /api/user/verify

        自动识别身份信息
        """
        user = r.user

        if user.verify_status != User.VERIFY_STATUS_UNVERIFIED:
            if user.verify_status == User.VERIFY_STATUS_UNDER_AUTO or \
                    user.verify_status == User.VERIFY_STATUS_UNDER_MANUAL:
                raise IDCardError.VERIFYING('无法继续识别')
            else:
                raise IDCardError.REAL_VERIFIED('无法继续识别')

        urls = user.get_card_urls()
        if not urls['front'] or not urls['back']:
            raise IDCardError.CARD_NOT_COMPLETE

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
        UserP.real_name.clone().rename('name'),
        UserP.birthday.clone().null(),
        UserP.idcard.clone().null(),
        UserP.male.clone().null(),
    ]

    @staticmethod
    @Analyse.r([
        *VERIFY_PARAMS,
        P('token', '认证口令').null(),
        P('auto', '自动认证').default(True).process(bool),
    ])
    @Auth.require_login(deny_auth_token=True)
    def post(r):
        """ POST /api/user/verify

        确认认证信息
        """
        user = r.user

        if user.verify_status != User.VERIFY_STATUS_UNVERIFIED:
            if user.verify_status == User.VERIFY_STATUS_UNDER_AUTO or \
                    user.verify_status == User.VERIFY_STATUS_UNDER_MANUAL:
                raise IDCardError.VERIFYING('无法继续确认')
            else:
                raise IDCardError.REAL_VERIFIED('无法继续确认')

        if r.d.auto:
            # 自动验证
            token = r.d.token
            dict_ = JWT.decrypt(token)
            if 'user_id' not in dict_:
                raise IDCardError.AUTO_VERIFY_FAILED
            if user.user_str_id != dict_['user_id']:
                raise IDCardError.AUTO_VERIFY_FAILED

            crt_time = datetime.datetime.now().timestamp()
            valid_start = datetime.datetime.strptime(dict_['valid_start'], '%Y-%m-%d').timestamp()
            valid_end = datetime.datetime.strptime(dict_['valid_end'], '%Y-%m-%d').timestamp()
            if valid_start > crt_time or crt_time > valid_end:
                raise IDCardError.CARD_VALID_EXPIRED

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
                if not getattr(r.d, param.name):
                    return PError.NULL_NOT_ALLOW(param.name, param.read_name)

            user.update_card_info(**r.d.dict('name', 'birthday', 'idcard', 'male'))
            user.update_verify_status(User.VERIFY_STATUS_UNDER_MANUAL)
            Email.real_verify(user, '')
        return user.d()


class DevView(View):
    @staticmethod
    @Auth.require_login(deny_auth_token=True)
    def post(r):
        user = r.user
        if user.verify_status != User.VERIFY_STATUS_DONE:
            return PremiseCheckerError.REQUIRE_REAL_VERIFY
        user.developer()
        return user.d()


def set_unique_user_str_id(_):
    for user in User.objects.all():
        user.user_str_id = User.get_unique_id()
        user.save()
