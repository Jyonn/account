import json

from django.views import View
from smartdjango import analyse, Validator

from App.models import UserApp
from App.params import AppParams
from App.validators import AppErrors
from Base.auth import Auth, AuthErrors
from Base.jtoken import JWType, JWT

OAUTH_TOKEN_EXPIRE_TIME = 30 * 24 * 60 * 60


def _redact(value, keep_start=6, keep_end=4):
    if value is None:
        return None
    text = str(value)
    if len(text) <= keep_start + keep_end:
        return text
    return '%s...%s' % (text[:keep_start], text[-keep_end:])


class OAuth(View):
    @analyse.query(AppParams.app)
    @Auth.require_login(deny_auth_token=True)
    def get(self, request):
        """GET /api/oauth/?app_id=:app_id"""
        print(
            '[account-backend][oauth] get',
            dict(
                user_id=getattr(request.user, 'user_str_id', None),
                app_id=getattr(request.query.app, 'id', None),
            ),
            flush=True,
        )
        # 可在新版本之后删除
        user = request.user
        app = request.query.app
        
        user_app = UserApp.get_by_user_app(user, app)
        if float(user_app.last_auth_code_time) < app.field_change_time:
            raise AuthErrors.APP_FIELD_CHANGE

        if user_app.bind:
            encode_str, dict_ = UserApp.do_bind(user, app)
            print(
                '[account-backend][oauth] get-success',
                dict(
                    user_app_id=user_app.user_app_id,
                    app_id=app.id,
                    auth_code=_redact(encode_str),
                    redirect_uri=app.redirect_uri,
                ),
                flush=True,
            )
            return dict(auth_code=encode_str, redirect_uri=app.redirect_uri)
        else:
            raise AppErrors.APP_NOT_BOUND

    @analyse.json(AppParams.app)
    @Auth.require_login(deny_auth_token=True)
    def post(self, request):
        """POST /api/oauth/

        授权应用
        """
        print(
            '[account-backend][oauth] post',
            dict(
                user_id=getattr(request.user, 'user_str_id', None),
                app_id=getattr(request.json.app, 'id', None),
            ),
            flush=True,
        )
        user = request.user
        app = request.json.app

        encode_str, dict_ = UserApp.do_bind(user, app)
        print(
            '[account-backend][oauth] post-success',
            dict(
                user_app_id=dict_.get('user_app_id'),
                app_id=app.id,
                auth_code=_redact(encode_str),
                redirect_uri=app.redirect_uri,
            ),
            flush=True,
        )
        return dict(auth_code=encode_str, redirect_uri=app.redirect_uri)


class OAuthToken(View):
    @analyse.json(
        Validator('code', '授权码'),
        AppParams.secret.copy().rename('app_secret')
    )
    def post(self, request):
        """POST /api/oauth/token"""
        code = request.json.code
        raw_json = request.json()
        app_secret = raw_json.get('app_secret')
        print(
            '[account-backend][oauth-token] request',
            dict(
                code=_redact(code),
                app_secret=_redact(app_secret),
            ),
            flush=True,
        )
        dict_ = JWT.decrypt(code)
        print(
            '[account-backend][oauth-token] decoded',
            dict(
                payload=json.dumps(dict_, ensure_ascii=False, default=str),
            ),
            flush=True,
        )
        if dict_['type'] != JWType.AUTH_CODE:
            raise AuthErrors.REQUIRE_AUTH_CODE

        user_app_id = dict_['user_app_id']
        user_app = UserApp.get_by_id(user_app_id, check_bind=True)
        print(
            '[account-backend][oauth-token] user-app',
            dict(
                user_app_id=user_app.user_app_id,
                app_id=user_app.app.id,
                secret_match=app_secret == user_app.app.secret,
                stored_last_auth_code_time=user_app.last_auth_code_time,
                app_field_change_time=user_app.app.field_change_time,
            ),
            flush=True,
        )

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
        print(
            '[account-backend][oauth-token] success',
            dict(
                user_app_id=user_app.user_app_id,
                app_id=user_app.app.id,
                token=_redact(token),
            ),
            flush=True,
        )

        return dict_
