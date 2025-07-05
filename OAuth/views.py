from django.views import View
from smartdjango import analyse, Validator

from App.models import UserApp
from App.params import AppParams
from App.validators import AppErrors
from Base.auth import Auth, AuthErrors
from Base.jtoken import JWType, JWT

OAUTH_TOKEN_EXPIRE_TIME = 30 * 24 * 60 * 60


class OAuth(View):
    @analyse.query(AppParams.app)
    @Auth.require_login(deny_auth_token=True)
    def get(self, request):
        """GET /api/oauth/?app_id=:app_id"""
        # 可在新版本之后删除
        user = request.user
        app = request.query.app
        
        user_app = UserApp.get_by_user_app(user, app)
        if float(user_app.last_auth_code_time) < app.field_change_time:
            raise AuthErrors.APP_FIELD_CHANGE

        if user_app.bind:
            encode_str, dict_ = UserApp.do_bind(user, app)
            return dict(auth_code=encode_str, redirect_uri=app.redirect_uri)
        else:
            raise AppErrors.APP_NOT_BOUND

    @analyse.body(AppParams.app)
    @Auth.require_login(deny_auth_token=True)
    def post(self, request):
        """POST /api/oauth/

        授权应用
        """
        user = request.user
        app = request.body.app

        encode_str, dict_ = UserApp.do_bind(user, app)
        return dict(auth_code=encode_str, redirect_uri=app.redirect_uri)


class OAuthToken(View):
    @analyse.body(
        Validator('code', '授权码'),
        AppParams.secret.copy().rename('app_secret')
    )
    def post(self, request):
        """POST /api/oauth/token"""
        code = request.body.code
        dict_ = JWT.decrypt(code)
        if dict_['type'] != JWType.AUTH_CODE:
            raise AuthErrors.REQUIRE_AUTH_CODE

        user_app_id = dict_['user_app_id']
        user_app = UserApp.get_by_id(user_app_id, check_bind=True)

        ctime = dict_['ctime']
        if user_app.app.field_change_time > ctime:
            raise AuthErrors.APP_FIELD_CHANGE

        if user_app.last_auth_code_time != str(ctime):
            raise AuthErrors.NEW_AUTH_CODE_CREATED

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
