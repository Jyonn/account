from functools import wraps

from smartdjango import analyse

from smartdjango import Error, Code

from Base.jtoken import JWT, JWType
from User.models import User


@Error.register
class AuthErrors:
    REQUIRE_LOGIN = Error("需要登录", code=Code.Unauthorized)
    TOKEN_MISS_PARAM = Error("认证口令缺少参数[{param}]", code=Code.BadRequest)
    APP_FIELD_CHANGE = Error("应用信息发生变化", code=Code.BadRequest)
    ERROR_TOKEN_TYPE = Error("错误的Token类型，登录失败", code=Code.Unauthorized)
    PASSWORD_CHANGED = Error("密码已修改，请重新登录", code=Code.Unauthorized)
    REQUIRE_ROOT = Error("需要管理员登录", code=Code.Unauthorized)
    DENY_ALL_AUTH_TOKEN = Error("拒绝第三方认证请求", code=Code.Unauthorized)
    SCOPE_NOT_SATISFIED = Error("没有获取权限：[{desc}]", code=Code.Unauthorized)
    REQUIRE_AUTH_CODE = Error("需要身份认证code", code=Code.Unauthorized)
    NEW_AUTH_CODE_CREATED = Error("授权失效", code=Code.BadRequest)


class Auth:
    @staticmethod
    def _parse_token(request):
        jwt_str = request.META.get('HTTP_TOKEN')
        if jwt_str is None:
            raise AuthErrors.REQUIRE_LOGIN
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
    def _extract_user(cls, request):
        request.user = None

        dict_ = Auth._parse_token(request)

        ctime = dict_.get('ctime')
        if not ctime:
            raise AuthErrors.TOKEN_MISS_PARAM(param='ctime')

        type_ = dict_.get('type')
        if not type_:
            raise AuthErrors.TOKEN_MISS_PARAM(param='type')

        if type_ == JWType.LOGIN_TOKEN:
            user_id = dict_.get('user_id')
            if not user_id:
                raise AuthErrors.TOKEN_MISS_PARAM(param='user_id')

            from User.models import User
            user = User.get_by_str_id(user_id)

        elif type_ == JWType.AUTH_TOKEN:
            user_app_id = dict_.get('user_app_id')
            if not user_app_id:
                raise AuthErrors.TOKEN_MISS_PARAM(param='user_app_id')

            from App.models import UserApp
            user_app = UserApp.get_by_id(user_app_id, check_bind=True)

            if float(user_app.app.field_change_time) > ctime:
                raise AuthErrors.APP_FIELD_CHANGE
            user = user_app.user
            request.user_app = user_app
        else:
            raise AuthErrors.ERROR_TOKEN_TYPE

        if float(user.pwd_change_time) > ctime:
            raise AuthErrors.PASSWORD_CHANGED

        request.user = user
        request.type_ = type_

    @classmethod
    def require_login(
            cls,
            scope_list=None,
            deny_auth_token=False,
            allow_no_login=False,
            require_root=False
    ):
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                _scope_list = scope_list or []
                request = analyse.get_request(*args)

                try:
                    cls._extract_user(request)
                except Exception as err:
                    if allow_no_login and not require_root:
                        return func(*args, **kwargs)
                    else:
                        raise AuthErrors.REQUIRE_LOGIN(details=err)

                if require_root:
                    user = request.user
                    from User.models import User
                    if user.pk != User.ROOT_ID:
                        raise AuthErrors.REQUIRE_ROOT

                if request.type_ != JWType.AUTH_TOKEN:
                    return func(*args, **kwargs)

                if deny_auth_token:
                    raise AuthErrors.DENY_ALL_AUTH_TOKEN

                app = request.user_app.app
                for score in _scope_list:
                    if score not in app.scopes.all():
                        raise AuthErrors.SCOPE_NOT_SATISFIED(desc=score.desc)
                return func(*args, **kwargs)

            return wrapper
        return decorator
