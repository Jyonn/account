from SmartDjango import Analyse, P
from django.views import View

from App.models import UserApp, AppError, AppP
from Base.auth import Auth, AuthError
from Base.jtoken import JWType, JWT

OAUTH_TOKEN_EXPIRE_TIME = 30 * 24 * 60 * 60


class OAuthView(View):
    @staticmethod
    @Analyse.r(q=[AppP.app])
    @Auth.require_login(deny_auth_token=True)
    def get(r):
        """GET /api/oauth/?app_id=:app_id"""
        # 可在新版本之后删除
        user = r.user
        app = r.d.app
        
        user_app = UserApp.get_by_user_app(user, app)
        if float(user_app.last_auth_code_time) < app.field_change_time:
            raise AuthError.APP_FIELD_CHANGE

        if user_app.bind:
            encode_str, dict_ = UserApp.do_bind(user, app)
            return dict(auth_code=encode_str, redirect_uri=app.redirect_uri)
        else:
            raise AppError.APP_UNBINDED

    @staticmethod
    @Analyse.r([AppP.app])
    @Auth.require_login(deny_auth_token=True)
    def post(r):
        """POST /api/oauth/

        授权应用
        """
        user = r.user
        app = r.d.app

        encode_str, dict_ = UserApp.do_bind(user, app)
        return dict(auth_code=encode_str, redirect_uri=app.redirect_uri)


class OAuthTokenView(View):
    @staticmethod
    @Analyse.r([P('code', '授权码'), AppP.secret.clone().rename('app_secret')])
    def post(r):
        """POST /api/oauth/token"""
        code = r.d.code
        dict_ = JWT.decrypt(code)
        if dict_['type'] != JWType.AUTH_CODE:
            raise AuthError.REQUIRE_AUTH_CODE

        user_app_id = dict_['user_app_id']
        user_app = UserApp.get_by_id(user_app_id, check_bind=True)

        ctime = dict_['ctime']
        if user_app.app.field_change_time > ctime:
            raise AuthError.APP_FIELD_CHANGE

        if user_app.last_auth_code_time != str(ctime):
            raise AuthError.NEW_AUTH_CODE_CREATED

        token, dict_ = JWT.encrypt(
            dict(
                user_app_id=user_app.user_app_id,
                type=JWType.AUTH_TOKEN,
            ),
            expire_second=OAUTH_TOKEN_EXPIRE_TIME,
        )
        dict_['token'] = token
        dict_['avatar'] = user_app.user.get_avatar_url()

        return dict_
