from django.views import View

from App.models import App, Scope
from Base.decorator import require_get, require_login, require_post, require_put, require_delete, \
    require_json
from Base.error import Error
from Base.response import error_response, response


class AppView(View):
    @staticmethod
    @require_get()
    @require_login
    def get(request):
        """GET /api/app

        获取app列表
        """
        o_user = request.user
        o_apps = App.get_apps_by_owner(o_user)
        app_list = [o_app.to_dict() for o_app in o_apps]

        return response(body=app_list)

    @staticmethod
    @require_json
    @require_post([
        'name',
        'redirect_uri',
        {
            "value": 'scopes',
            "process": Scope.list_to_scope_list,
        }
    ])
    @require_login
    def post(request):
        o_user = request.user
        name = request.d.name
        redirect_uri = request.d.redirect_uri
        scopes = request.d.scopes

        ret = App.create(name, redirect_uri, scopes, o_user)
        if ret.error is not Error.OK:
            return error_response(ret)
        o_app = ret.body
        return response(o_app.to_dict())


class AppIDView(View):
    @staticmethod
    @require_json
    @require_put([('name', None, None), ('redirect_uri', None, None)])
    @require_login
    def put(request, app_id):
        o_user = request.user
        name = request.d.name
        redirect_uri = request.d.redirect_uri

        ret = App.get_app_by_id(app_id)
        if ret.error is not Error.OK:
            return error_response(ret)
        o_app = ret.body
        if o_app.owner is not o_user:
            return error_response(Error.APP_NOT_BELONG)

        ret = o_app.modify(name, redirect_uri)
        if ret.error is not Error.OK:
            return error_response(ret)
        return response(body=o_app.to_dict())

    @staticmethod
    @require_delete()
    @require_login
    def delete(request, app_id):
        o_user = request.user

        ret = App.get_app_by_id(app_id)
        if ret.error is not Error.OK:
            return error_response(ret)
        o_app = ret.body
        if o_app.owner is not o_user:
            return error_response(Error.APP_NOT_BELONG)

        o_app.delete()
        return response()
