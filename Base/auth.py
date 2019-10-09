from functools import wraps

from SmartDjango import Excp, E

from Base.jtoken import JWT, JWType
from User.models import User


@E.register
class AuthError:
    REQUIRE_LOGIN = E("需要登录")
    TOKEN_MISS_PARAM = E("认证口令缺少参数{0}", E.PH_FORMAT)
    APP_FIELD_CHANGE = E("应用信息发生变化")
    ERROR_TOKEN_TYPE = E("错误的Token类型，登录失败")
    PASSWORD_CHANGED = E("密码已修改，请重新登录")
    REQUIRE_ROOT = E("需要管理员登录")
    DENY_ALL_AUTH_TOKEN = E("拒绝第三方认证请求")
    SCOPE_NOT_SATISFIED = E("没有获取权限：")
    REQUIRE_AUTH_CODE = E("需要身份认证code")
    NEW_AUTH_CODE_CREATED = E("授权失效")


class Auth:
    @staticmethod
    @Excp.pack
    def validate_token(r):
        jwt_str = r.META.get('HTTP_TOKEN')
        if jwt_str is None:
            return AuthError.REQUIRE_LOGIN
        return JWT.decrypt(jwt_str)

    @staticmethod
    def get_login_token(user: User):
        token, dict_ = JWT.encrypt(dict(
            type=JWType.LOGIN_TOKEN,
            user_id=user.user_str_id,
        ))
        dict_['token'] = token
        dict_['user'] = user.d()
        return dict_

    @classmethod
    @Excp.pack
    def _extract_user(cls, r):
        r.user = None

        dict_ = Auth.validate_token(r)

        ctime = dict_.get('ctime')
        if not ctime:
            return AuthError.TOKEN_MISS_PARAM('ctime')

        type_ = dict_.get('type')
        if not type_:
            return AuthError.TOKEN_MISS_PARAM('type')

        if type_ == JWType.LOGIN_TOKEN:
            user_id = dict_.get('user_id')
            if not user_id:
                return AuthError.TOKEN_MISS_PARAM('user_id')

            from User.models import User
            user = User.get_by_str_id(user_id)

        elif type_ == JWType.AUTH_TOKEN:
            user_app_id = dict_.get('user_app_id')
            if not user_app_id:
                return AuthError.TOKEN_MISS_PARAM('user_app_id')

            from App.models import UserApp
            user_app = UserApp.get_by_id(user_app_id, check_bind=True)

            if float(user_app.app.field_change_time) > ctime:
                return AuthError.APP_FIELD_CHANGE
            user = user_app.user
            r.user_app = user_app
        else:
            return AuthError.ERROR_TOKEN_TYPE

        if float(user.pwd_change_time) > ctime:
            return AuthError.PASSWORD_CHANGED

        r.user = user
        r.type_ = type_

    @classmethod
    def require_login(cls, scope_list=None, deny_auth_token=False, allow_no_login=False,
                      require_root=False):
        def decorator(func):
            @wraps(func)
            @Excp.pack
            def wrapper(r, *args, **kwargs):
                _scope_list = scope_list or []

                try:
                    cls._extract_user(r)
                except Exception as err:
                    if allow_no_login and not require_root:
                        return func(r, *args, **kwargs)
                    else:
                        return AuthError.REQUIRE_LOGIN

                if require_root:
                    user = r.user
                    from User.models import User
                    if user.pk != User.ROOT_ID:
                        return AuthError.REQUIRE_ROOT

                if r.type_ != JWType.AUTH_TOKEN:
                    return func(r, *args, **kwargs)

                if deny_auth_token:
                    return AuthError.DENY_ALL_AUTH_TOKEN

                app = r.user_app.app
                for score in _scope_list:
                    if score not in app.scopes.all():
                        return AuthError.SCOPE_NOT_SATISFIED(score.desc)
                return func(r, *args, **kwargs)

            return wrapper
        return decorator
