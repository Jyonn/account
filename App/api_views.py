from django.views import View

from App.models import App, Scope, UserApp, Premise
from Base.policy import Policy
from Base.qn import QN_PUBLIC_MANAGER
from Base.scope import ScopeInstance
from Base.valid_param import ValidParam
from Base.validator import require_param, require_json, require_login
from Base.error import Error
from Base.response import error_response, response
from User.models import User

VP_APP_NAME = ValidParam('name', '应用名称')
VP_APP_INFO = ValidParam('info', '应用详细信息')
VP_APP_DESC = ValidParam('description', '应用标语')
VP_APP_URI = ValidParam('redirect_uri', '应用回调地址')
VP_APP_SCOPE = ValidParam('scopes').p(Scope.list_to_scope_list).r('应用权限列表')
VP_APP_PREMISE = ValidParam('premises').p(Premise.list_to_premise_list).r('应用要求列表')
VP_APP_ID = ValidParam('app_id', '应用ID')
VP_APP_SECRET = ValidParam('app_secret', '应用密钥')


class AppView(View):
    @staticmethod
    def relation_process(relation):
        if relation not in App.R_LIST:
            relation = App.R_USER
        return relation

    @staticmethod
    @require_param(q=[
        ValidParam('relation').df(App.R_USER).p(relation_process),
        ValidParam('frequent').df(),
        ValidParam('count').df(3).p(int),
    ])
    @require_login([ScopeInstance.read_app_list])
    def get(request):
        """ GET /api/app/

        获取与我相关的app列表
        """
        o_user = request.user
        relation = request.d.relation

        if relation == App.R_OWNER:
            o_apps = App.get_apps_by_owner(o_user)
            app_list = [o_app.to_dict(base=True) for o_app in o_apps]
        else:
            frequent = request.d.frequent
            count = request.d.count
            user_app_list = UserApp.get_user_app_list_by_o_user(o_user, frequent, count)
            app_list = [o_user_app.app.to_dict(base=True) for o_user_app in user_app_list]
        return response(body=app_list)

    @staticmethod
    @require_json
    @require_param([VP_APP_NAME, VP_APP_DESC, VP_APP_URI, VP_APP_SCOPE, VP_APP_PREMISE])
    @require_login(deny_auth_token=True)
    def post(request):
        """ POST /api/app/

        创建我的app
        """
        o_user = request.user
        name = request.d.name
        description = request.d.description
        redirect_uri = request.d.redirect_uri
        scopes = request.d.scopes
        premises = request.d.premises

        ret = App.create(name, description, redirect_uri, scopes, premises, o_user)
        if ret.error is not Error.OK:
            return error_response(ret)
        o_app = ret.body
        return response(body=o_app.to_dict(base=True))


class AppIDSecretView(View):
    @staticmethod
    @require_login(deny_auth_token=True)
    def get(request, app_id):
        """ GET /api/app/:app_id/secret"""
        o_user = request.user

        ret = App.get_app_by_id(app_id)
        if ret.error is not Error.OK:
            return error_response(ret)
        o_app = ret.body
        if not isinstance(o_app, App):
            return error_response(Error.STRANGE)

        if not o_app.belong(o_user):
            return error_response(Error.APP_NOT_BELONG)

        return response(body=o_app.secret)


class AppIDView(View):
    @staticmethod
    @require_login(deny_auth_token=True, allow_no_login=True)
    def get(request, app_id):
        """ GET /api/app/:app_id

        获取应用信息以及用户与应用的关系（属于、绑定、打分，仅限用户登录时）
        """
        o_user = request.user

        ret = App.get_app_by_id(app_id)
        if ret.error is not Error.OK:
            return error_response(ret)
        o_app = ret.body
        if not isinstance(o_app, App):
            return error_response(Error.STRANGE)

        dict_ = o_app.to_dict(o_user=o_user)

        ret = UserApp.get_user_app_by_o_user_o_app(o_user, o_app)
        if ret.error is not Error.OK:
            relation = dict(bind=False, rebind=False, mark=0, belong=False, user_app_id=None)
        else:
            o_user_app = ret.body
            if not isinstance(o_user_app, UserApp):
                return error_response(Error.STRANGE)
            relation = o_user_app.to_dict()

        relation['belong'] = o_app.belong(o_user)
        dict_['relation'] = relation

        dict_['belong'] = relation['belong']  # 老版本兼容

        return response(body=dict_)

    @staticmethod
    @require_json
    @require_param([VP_APP_NAME, VP_APP_INFO, VP_APP_DESC, VP_APP_URI, VP_APP_SCOPE, VP_APP_PREMISE])
    @require_login(deny_auth_token=True)
    def put(request, app_id):
        """ PUT /api/app/:app_id

        修改应用信息
        """
        o_user = request.user
        name = request.d.name
        desc = request.d.description
        info = request.d.info
        redirect_uri = request.d.redirect_uri
        scopes = request.d.scopes
        premises = request.d.premises

        ret = App.get_app_by_id(app_id)
        if ret.error is not Error.OK:
            return error_response(ret)
        o_app = ret.body
        if not isinstance(o_app, App):
            return error_response(Error.STRANGE)

        if not o_app.belong(o_user):
            return error_response(Error.APP_NOT_BELONG)

        ret = o_app.modify(name, desc, info, redirect_uri, scopes, premises)
        if ret.error is not Error.OK:
            return error_response(ret)
        return response(body=o_app.to_dict(o_user=o_user))

    @staticmethod
    @require_param()
    @require_login(deny_auth_token=True)
    def delete(request, app_id):
        """ DELETE /api/app/:app_id

        删除应用
        """
        o_user = request.user

        ret = App.get_app_by_id(app_id)
        if ret.error is not Error.OK:
            return error_response(ret)
        o_app = ret.body
        if not o_app.belong(o_user):
            return error_response(Error.APP_NOT_BELONG)

        o_app.delete()
        return response()


class ScopeView(View):
    @staticmethod
    def get(request):
        return response(body=Scope.get_scope_list())


class PremiseView(View):
    @staticmethod
    def get(request):
        return response(body=Premise.get_premise_list())


class AppLogoView(View):
    @staticmethod
    @require_param(q=[
        ValidParam('filename', '文件名'),
        VP_APP_ID,
    ])
    @require_login(deny_auth_token=True)
    def get(request):
        """ GET /api/app/logo

        获取七牛上传token
        """
        o_user = request.user
        if not isinstance(o_user, User):
            return error_response(Error.STRANGE)

        filename = request.d.filename
        app_id = request.d.app_id

        ret = App.get_app_by_id(app_id)
        if ret.error is not Error.OK:
            return error_response(ret)
        o_app = ret.body
        if not isinstance(o_app, App):
            return error_response(Error.STRANGE)

        if o_app.owner != o_user:
            return error_response(Error.APP_NOT_BELONG)

        import datetime
        crt_time = datetime.datetime.now().timestamp()
        key = 'app/%s/logo/%s/%s' % (app_id, crt_time, filename)
        qn_token, key = QN_PUBLIC_MANAGER.get_upload_token(key, Policy.logo(app_id))
        return response(body=dict(upload_token=qn_token, key=key))

    @staticmethod
    @require_json
    @require_param([
        ValidParam('key', '七牛存储键'),
        VP_APP_ID
    ])
    def post(request):
        """ POST /api/app/logo

        七牛上传应用logo回调函数
        """
        ret = QN_PUBLIC_MANAGER.qiniu_auth_callback(request)
        if ret.error is not Error.OK:
            return error_response(ret)

        key = request.d.key
        app_id = request.d.app_id
        ret = App.get_app_by_id(app_id)
        if ret.error is not Error.OK:
            return error_response(ret)
        o_app = ret.body
        if not isinstance(o_app, App):
            return error_response(Error.STRANGE)
        o_app.modify_logo(key)
        return response(body=o_app.to_dict())


class UserAppIdView(View):
    @staticmethod
    @require_json
    @require_param([VP_APP_SECRET])
    def post(request, user_app_id):
        """ POST /api/app/user/:user_app_id

        通过app获取user信息
        """

        app_secret = request.d.app_secret

        ret = UserApp.get_user_app_by_user_app_id(user_app_id)
        if ret.error is not Error.OK:
            return error_response(ret)
        o_user_app = ret.body
        if not isinstance(o_user_app, UserApp):
            return error_response(Error.STRANGE)

        if not o_user_app.app.authentication(app_secret):
            return error_response(Error.ERROR_APP_SECRET)

        return response(body=o_user_app.user.to_dict())

    @staticmethod
    @require_json
    @require_param([ValidParam('mark', '应用评分').p(int)])
    @require_login(deny_auth_token=True)
    def put(request, user_app_id):
        """ PUT /api/app/user/:user_app_id

        给app评分
        """
        ret = UserApp.get_user_app_by_user_app_id(user_app_id)
        if ret.error is not Error.OK:
            return error_response(ret)
        o_user_app = ret.body
        if not isinstance(o_user_app, UserApp):
            return error_response(Error.STRANGE)
        if o_user_app.user.user_str_id != request.user.user_str_id:
            return error_response(Error.ILLEGAL_ACCESS_RIGHT)
        mark = request.d.mark

        ret = o_user_app.do_mark(mark)
        if ret.error is not Error.OK:
            return error_response(ret)
        return response(body=list(map(int, o_user_app.app.mark.split('-'))))


@require_param(method='GET')
def refresh_frequent_score(request):
    """ GET /api/app/refresh-frequent-score

    更新用户应用的使用频率度，判断是否为常用应用
    """
    ret = UserApp.refresh_frequent_score()
    return error_response(ret)
