from django.views import View

from App.models import App, UserApp
from Base.common import deprint
from Base.validator import require_post, require_login, require_scope
from Base.error import Error
from Base.jtoken import jwt_d, JWType, jwt_e
from Base.response import error_response, response


class OAuthView(View):
    @staticmethod
    @require_post(['app_id'])
    @require_login
    @require_scope(deny_all_auth_token=True)
    def post(request):
        """POST /api/oauth/"""
        o_user = request.user
        app_id = request.d.app_id

        ret = App.get_app_by_id(app_id)
        if ret.error is not Error.OK:
            return error_response(ret)
        o_app = ret.body
        if not isinstance(o_app, App):
            return error_response(Error.STRANGE)

        ret = UserApp.do_bind(o_user, o_app)
        if ret.error is not Error.OK:
            return error_response(ret)
        return response(body=dict(auth_code=ret.body[0], redirect_uri=o_app.redirect_uri))


class OAuthTokenView(View):
    @staticmethod
    @require_post(['code', 'app_secret'])
    def post(request):
        """POST /api/oauth/token"""
        code = request.d.code
        ret = jwt_d(code)
        if ret.error is not Error.OK:
            return error_response(ret)
        dict_ = ret.body
        if dict_['type'] != JWType.AUTH_CODE:
            return error_response(Error.REQUIRE_AUTH_CODE)

        user_app_id = dict_['user_app_id']
        ret = UserApp.get_user_app_by_user_app_id(user_app_id, check_bind=True)
        if ret.error is not Error.OK:
            return error_response(ret)
        o_user_app = ret.body
        if not isinstance(o_user_app, UserApp):
            deprint('OAuth-api_views-OAuthTokenView-post-UserApp.get_user_app_by_user_app_id',
                    user_app_id)
            return error_response(Error.STRANGE)

        ctime = dict_['ctime']
        if o_user_app.app.field_change_time > ctime:
            return error_response(Error.APP_FIELD_CHANGE)
        print(o_user_app.last_auth_code_time, type(o_user_app.last_auth_code_time))
        print(ctime, type(ctime))

        if abs(o_user_app.last_auth_code_time - ctime) > 1e5:
            return error_response(Error.NEW_AUTH_CODE_CREATED)

        ret = jwt_e(
            dict(
                user_app_id=o_user_app.user_app_id,
                type=JWType.AUTH_TOKEN,
            ),
            expire_second=365 * 24 * 60 * 60
        )
        if ret.error is not Error.OK:
            return error_response(ret)
        token, dict_ = ret.body
        dict_['token'] = token
        dict_['avatar'] = o_user_app.user.get_avatar_url()

        return response(body=dict_)
