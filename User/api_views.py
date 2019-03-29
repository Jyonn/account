""" Adel Liu 180228

用户API处理函数
"""
import datetime

from django.views import View

from Base.common import deprint
from Base.idcard import IDCard
from Base.mail import Email
from Base.scope import ScopeInstance
from Base.valid_param import ValidParam
from Base.validator import require_json, require_param, require_login
from Base.error import Error
from Base.jtoken import jwt_e, JWType, jwt_d
from Base.policy import Policy
from Base.qn import QN_PUBLIC_MANAGER, QN_RES_MANAGER
from Base.response import response, error_response
from Base.send_mobile import SendMobile
from Base.session import Session

from User.models import User


VP_BACK = ValidParam('back', '侧别').p(int)


class UserView(View):
    @staticmethod
    def get_token_info(o_user):
        ret = jwt_e(dict(user_id=o_user.user_str_id, type=JWType.LOGIN_TOKEN))
        if ret.error is not Error.OK:
            return error_response(ret)
        token, dict_ = ret.body
        dict_['token'] = token
        dict_['user'] = o_user.to_dict()
        return dict_

    @staticmethod
    @require_login([ScopeInstance.read_base_info])
    def get(request):
        """ GET /api/user/

        获取我的信息
        """
        o_user = request.user
        if not isinstance(o_user, User):
            deprint('User-api_views-UserView-get-o_user-User')
            return error_response(Error.STRANGE)
        return response(body=o_user.to_dict(oauth=request.type_ == JWType.AUTH_TOKEN))

    @staticmethod
    @require_json
    @require_param([
        ValidParam('password', '密码'),
        ValidParam('code', '验证码')
    ])
    def post(request):
        """ POST /api/user/

        创建用户
        """
        code = request.d.code
        password = request.d.password

        ret = SendMobile.check_captcha(request, code)
        if ret.error is not Error.OK:
            return error_response(ret)
        phone = ret.body

        ret = User.create(phone, password)
        if ret.error is not Error.OK:
            return error_response(ret)
        o_user = ret.body
        if not isinstance(o_user, User):
            return error_response(Error.STRANGE)

        return response(body=UserView.get_token_info(o_user))

    @staticmethod
    @require_json
    @require_param(
        [
            ValidParam('password').df().r('新密码'),
            ValidParam('old_password').df().r('旧密码'),
            ValidParam('nickname').df().r('昵称'),
            ValidParam('description').df().r('个性签名'),
            ValidParam('qitian').df().r('齐天号'),
            ValidParam('birthday').df().r('生日'),
        ]
    )
    @require_login(deny_auth_token=True)
    def put(request):
        """ PUT /api/user/

        修改用户信息
        """
        o_user = request.user
        if not isinstance(o_user, User):
            return error_response(Error.STRANGE)

        password = request.d.password
        nickname = request.d.nickname
        qitian = request.d.qitian
        old_password = request.d.old_password
        description = request.d.description
        birthday = request.d.birthday
        if password is not None:
            ret = o_user.change_password(password, old_password)
            if ret.error is not Error.OK:
                return error_response(ret)
        try:
            birthday = datetime.datetime.strptime(birthday, '%Y-%m-%d')
        except Exception as err:
            deprint(str(err))
            return error_response(Error.ERROR_BIRTHDAY_FORMAT)
        if birthday.timestamp() > datetime.datetime.now().timestamp():
            return error_response(Error.ERROR_BIRTHDAY_FORMAT)
        ret = o_user.modify_info(nickname, description, qitian, birthday.date())
        if ret.error is not Error.OK:
            return error_response(ret)
        return response(body=o_user.to_dict())


class TokenView(View):
    @staticmethod
    @require_json
    @require_param([ValidParam('password', '密码')])
    def post(request):
        """ POST /api/user/token

        登录获取token
        """
        password = request.d.password
        login_type = Session.load(request, SendMobile.LOGIN_TYPE, once_delete=False)
        if not login_type:
            return error_response(Error.ERROR_SESSION)
        login_value = Session.load(request, login_type, once_delete=False)
        if not login_value:
            return error_response(Error.ERROR_SESSION)
        if login_type == SendMobile.PHONE_NUMBER:
            ret = User.authenticate(None, login_value, password)
        else:
            ret = User.authenticate(login_value, None, password)
        if ret.error != Error.OK:
            return error_response(ret)
        o_user = ret.body
        if not isinstance(o_user, User):
            return error_response(Error.STRANGE)

        return response(body=UserView.get_token_info(o_user))


class AvatarView(View):
    @staticmethod
    @require_param(q=[ValidParam('filename', '文件名')])
    @require_login(deny_auth_token=True)
    def get(request):
        """ GET /api/user/avatar

        获取七牛上传token
        """
        o_user = request.user
        filename = request.d.filename

        if not isinstance(o_user, User):
            return error_response(Error.STRANGE)

        import datetime
        crt_time = datetime.datetime.now().timestamp()
        key = 'user/%s/avatar/%s/%s' % (o_user.user_str_id, crt_time, filename)
        qn_token, key = QN_PUBLIC_MANAGER.get_upload_token(key, Policy.avatar(o_user.user_str_id))
        return response(body=dict(upload_token=qn_token, key=key))

    @staticmethod
    @require_json
    @require_param([
        ValidParam('key', '七牛存储键'),
        ValidParam('user_id', '用户ID')
    ])
    def post(request):
        """ POST /api/user/avatar

        七牛上传用户头像回调函数
        """
        ret = QN_PUBLIC_MANAGER.qiniu_auth_callback(request)
        if ret.error is not Error.OK:
            return error_response(ret)

        key = request.d.key
        user_id = request.d.user_id
        ret = User.get_user_by_str_id(user_id)
        if ret.error is not Error.OK:
            return error_response(ret)
        o_user = ret.body
        if not isinstance(o_user, User):
            return error_response(Error.STRANGE)
        ret = o_user.modify_avatar(key)
        if ret.error is not Error.OK:
            return error_response(ret)
        return response(body=o_user.to_dict())


class IDCardView(View):
    @staticmethod
    @require_param(q=[ValidParam('filename', '文件名'), VP_BACK])
    @require_login(deny_auth_token=True)
    def get(request):
        """ GET /api/user/idcard?back=[0, 1]

        获取七牛上传token
        """
        o_user = request.user
        filename = request.d.filename
        back = int(bool(request.d.back))

        if o_user.verify_status != User.VERIFY_STATUS_UNVERIFIED:
            if o_user.verify_status == User.VERIFY_STATUS_UNDER_AUTO or o_user.verify_status == User.VERIFY_STATUS_UNDER_MANUAL:
                return error_response(Error.VERIFYING, append_msg='，无法重新上传')
            else:
                return error_response(Error.REAL_VERIFIED, append_msg='，无法重新上传')

        if not isinstance(o_user, User):
            return error_response(Error.STRANGE)

        import datetime
        crt_time = datetime.datetime.now().timestamp()
        key = 'user/%s/card/%s/%s/%s' % (o_user.user_str_id, ['front', 'back'][back], crt_time, filename)
        policy = Policy.verify_back if back else Policy.verify_front
        qn_token, key = QN_RES_MANAGER.get_upload_token(key, policy(o_user.user_str_id))
        return response(body=dict(upload_token=qn_token, key=key))

    @staticmethod
    @require_json
    @require_param(b=[
        ValidParam('key', '七牛存储键'),
        ValidParam('user_id', '用户ID'),
    ], q=[VP_BACK])
    def post(request):
        """ POST /api/user/idcard?back=[0, 1]

        七牛上传用户实名认证回调函数
        """
        ret = QN_PUBLIC_MANAGER.qiniu_auth_callback(request)
        if ret.error is not Error.OK:
            return error_response(ret)

        key = request.d.key
        user_id = request.d.user_id
        back = request.d.back

        ret = User.get_user_by_str_id(user_id)
        if ret.error is not Error.OK:
            return error_response(ret)
        o_user = ret.body
        if not isinstance(o_user, User):
            return error_response(Error.STRANGE)

        if o_user.verify_status != User.VERIFY_STATUS_UNVERIFIED:
            if o_user.verify_status == User.VERIFY_STATUS_UNDER_AUTO or \
                    o_user.verify_status == User.VERIFY_STATUS_UNDER_MANUAL:
                return error_response(Error.VERIFYING, append_msg='，无法重新上传')
            else:
                return error_response(Error.REAL_VERIFIED, append_msg='，无法重新上传')

        if back:
            ret = o_user.upload_verify_back(key)
        else:
            ret = o_user.upload_verify_front(key)
        if ret.error is not Error.OK:
            return error_response(ret)
        return response(body=ret.body)


class VerifyView(View):
    @staticmethod
    @require_login(deny_auth_token=True)
    def get(request):
        """ GET /api/user/verify

        自动识别身份信息
        """
        o_user = request.user
        if not isinstance(o_user, User):
            return error_response(Error.STRANGE)

        if o_user.verify_status != User.VERIFY_STATUS_UNVERIFIED:
            if o_user.verify_status == User.VERIFY_STATUS_UNDER_AUTO or \
                    o_user.verify_status == User.VERIFY_STATUS_UNDER_MANUAL:
                return error_response(Error.VERIFYING, append_msg='，无法继续识别')
            else:
                return error_response(Error.REAL_VERIFIED, append_msg='，无法继续识别')

        urls = o_user.get_card_urls()
        if not urls['front'] or not urls['back']:
            return error_response(Error.CARD_NOT_COMPLETE)

        ret = IDCard.detect_front(urls['front'])
        if ret.error is not Error.OK:
            return error_response(ret)
        front_info = ret.body
        ret = IDCard.detect_back(urls['back'])
        if ret.error is not Error.OK:
            return error_response(ret)
        back_info = ret.body

        back_info.update(front_info)
        back_info['type'] = 'idcard-verify'
        back_info['user_id'] = o_user.user_str_id
        ret = jwt_e(back_info, expire_second=60 * 5)
        if ret.error is not Error.OK:
            return ret
        token, verify_info = ret.body
        verify_info['token'] = token
        o_user.update_verify_type(User.VERIFY_CHINA)
        return response(body=verify_info)

    @staticmethod
    @require_param([
        ValidParam('name', '真实姓名').df(),
        ValidParam('birthday', '生日').df(),
        ValidParam('idcard', '身份证号').df(),
        ValidParam('male', '性别').df().p(bool),
        ValidParam('token', '认证口令').df(),
        ValidParam('auto', '自动认证').df(True).p(bool),
    ])
    @require_login(deny_auth_token=True)
    def post(request):
        """ POST /api/user/verify

        确认认证信息
        """
        o_user = request.user
        if not isinstance(o_user, User):
            return error_response(Error.STRANGE)

        if o_user.verify_status != User.VERIFY_STATUS_UNVERIFIED:
            if o_user.verify_status == User.VERIFY_STATUS_UNDER_AUTO or \
                    o_user.verify_status == User.VERIFY_STATUS_UNDER_MANUAL:
                return error_response(Error.VERIFYING, append_msg='，无法继续确认')
            else:
                return error_response(Error.REAL_VERIFIED, append_msg='，无法继续确认')

        if request.d.auto:
            # 自动验证
            token = request.d.token
            ret = jwt_d(token)
            if ret.error is not Error.OK:
                return error_response(ret)
            if 'user_id' not in ret.body:
                return error_response(Error.AUTO_VERIFY_FAILED)
            if o_user.user_str_id != ret.body['user_id']:
                return error_response(Error.AUTO_VERIFY_FAILED)

            crt_time = datetime.datetime.now().timestamp()
            valid_start = datetime.datetime.strptime(ret.body['valid_start'], '%Y-%m-%d').timestamp()
            valid_end = datetime.datetime.strptime(ret.body['valid_end'], '%Y-%m-%d').timestamp()
            if valid_start > crt_time or crt_time > valid_end:
                return error_response(Error.CARD_VALID_EXPIRED)

            ret = o_user.update_card_info(
                ret.body['name'],
                ret.body['male'],
                ret.body['idcard'],
                datetime.datetime.strptime(ret.body['birthday'], '%Y-%m-%d').date(),
            )
            if ret.error is not Error.OK:
                return error_response(ret)
            o_user.update_verify_status(User.VERIFY_STATUS_DONE)
        else:
            # 人工验证
            name = request.d.name
            birthday = request.d.birthday
            idcard = request.d.idcard
            male = request.d.male
            if not (name and birthday and idcard and male):
                return error_response(Error.REQUIRE_PARAM, append_msg='，人工验证信息不全')
            ret = o_user.update_card_info(
                name, male, idcard, datetime.datetime.strptime(birthday, '%Y-%m-%d').date(),
            )
            if ret.error is not Error.OK:
                return error_response(ret)
            o_user.update_verify_status(User.VERIFY_STATUS_UNDER_MANUAL)
            Email.real_verify(o_user, '')
        return response(body=o_user.to_dict())


def set_unique_user_str_id(request):
    for o_user in User.objects.all():
        # if not o_user.user_str_id:
        o_user.user_str_id = User.get_unique_user_str_id()
        o_user.save()
    return response()
