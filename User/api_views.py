""" Adel Liu 180228

用户API处理函数
"""
from django.views import View

from Base.common import deprint
from Base.scope import ScopeInstance
from Base.valid_param import ValidParam
from Base.validator import require_json, require_post, require_get, \
    require_put, require_login
from Base.error import Error
from Base.jtoken import jwt_e, JWType
from Base.policy import get_avatar_policy
from Base.qn import QN_PUBLIC_MANAGER
from Base.response import response, error_response
from Base.send_mobile import SendMobile
from Base.session import Session

from User.models import User


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
    @require_get()
    @require_login([ScopeInstance.r_base_info])
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
    @require_post([
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
    @require_put(
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
        ret = o_user.modify_info(nickname, description, qitian, birthday)
        if ret.error is not Error.OK:
            return error_response(ret)
        return response(body=o_user.to_dict())


class TokenView(View):
    @staticmethod
    @require_json
    @require_post([ValidParam('password', '密码')])
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
    @require_get([ValidParam('filename', '文件名')])
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
        qn_token, key = QN_PUBLIC_MANAGER.get_upload_token(key, get_avatar_policy(o_user.user_str_id))
        return response(body=dict(upload_token=qn_token, key=key))

    @staticmethod
    @require_json
    @require_post([
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
        o_user.modify_avatar(key)
        return response(body=o_user.to_dict())


def set_unique_user_str_id(request):
    for o_user in User.objects.all():
        # if not o_user.user_str_id:
        o_user.user_str_id = User.get_unique_user_str_id()
        o_user.save()
    return response()
