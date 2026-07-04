import datetime

from django.views import View
from smartdjango import analyse, Validator

from App.models import App, Scope, Premise
from App.params import AppParams
from App.services import AppService
from Base.auth import Auth
from Base.qn import qn_public_manager
from Base.scope import SI


def relation_process(relation):
    if relation not in App.R_LIST:
        relation = App.R_USER
    return relation


class AppView(View):
    @analyse.query(
        Validator('relation').default(App.R_USER).to(relation_process),
        Validator('frequent').null().default(None),
        Validator('count').default(3).to(int),
        Validator('last_time').null().to(float).to(datetime.datetime.fromtimestamp).default(None),
    )
    @Auth.require_login([SI.read_app_list])
    def get(self, request):
        """ GET /api/app/

        获取与我相关的app列表
        """
        return AppService.list_related_apps(
            user=request.user,
            relation=request.query.relation,
            frequent=request.query.frequent,
            count=request.query.count,
            last_time=request.query.last_time,
        )

    @analyse.json(
        AppParams.name,
        AppParams.desc,
        AppParams.redirect_uri,
        AppParams.test_redirect_uri,
        AppParams.scopes,
        AppParams.premises
    )
    @Auth.require_login(deny_auth_token=True)
    def post(self, request):
        """ POST /api/app/

        创建我的app
        """
        return AppService.create_app(owner=request.user, payload=request.json())


class AppListView(View):
    @staticmethod
    def get(_):
        """GET /app/list"""
        return App.list()


class AppIDSecret(View):
    @analyse.argument(AppParams.app)
    @Auth.require_login(deny_auth_token=True)
    def get(self, request, **kwargs):
        """ GET /api/app/:app_id/secret"""
        return AppService.get_secret(request.user, request.argument.app)


class AppID(View):
    @analyse.argument(AppParams.app)
    @Auth.require_login(deny_auth_token=True, allow_no_login=True)
    def get(self, request, **kwargs):
        """ GET /api/app/:app_id

        获取应用信息以及用户与应用的关系（属于、绑定、打分，仅限用户登录时）
        """
        return AppService.get_detail(request.user, request.argument.app)

    @analyse.json(
        AppParams.name.copy().null().default(None),
        AppParams.info.copy().null().default(None),
        AppParams.desc.copy().null().default(None),
        AppParams.redirect_uri.copy().null().default(None),
        AppParams.scopes.copy().null().default(None),
        AppParams.premises.copy().null().default(None),
        AppParams.test_redirect_uri.copy().null().default(None),
        AppParams.max_user_num,
    )
    @analyse.argument(AppParams.app)
    @Auth.require_login(deny_auth_token=True)
    def put(self, request, **kwargs):
        """ PUT /api/app/:app_id

        修改应用信息
        """
        return AppService.update_app(
            user=request.user,
            app=request.argument.app,
            payload=request.json(),
        )

    @analyse.argument(AppParams.app)
    @Auth.require_login(deny_auth_token=True)
    def delete(self, request, **kwargs):
        """ DELETE /api/app/:app_id

        删除应用
        """
        return AppService.delete_app(request.user, request.argument.app)


class ScopeView(View):
    def get(self, request):
        scopes = Scope.objects.all()
        return [scope.d() for scope in scopes]


class PremiseView(View):
    def get(self, request):
        premises = Premise.objects.all()
        return [premise.d() for premise in premises]


class AppLogoView(View):
    @analyse.query(Validator('filename', '文件名'), AppParams.app)
    @Auth.require_login(deny_auth_token=True)
    def get(self, request):
        """ GET /api/app/logo

        获取七牛上传token
        """
        return AppService.get_logo_upload_token(
            user=request.user,
            filename=request.query.filename,
            app=request.query.app,
        )

    @analyse.json(Validator('key', '七牛存储键'), AppParams.app)
    def post(self, request):
        """ POST /api/app/logo

        七牛上传应用logo回调函数
        """
        qn_public_manager.auth_callback(request)

        key = request.json.key
        app = request.json.app
        return AppService.handle_logo_uploaded(app, key)


class UserAppIdView(View):
    @analyse.json(AppParams.secret.copy().rename('app_secret'))
    @analyse.argument(AppParams.user_app)
    def post(self, request, **kwargs):
        """ POST /api/app/user/:user_app_id

        通过app获取user信息
        """

        return AppService.authenticate_user_app(
            user_app=request.argument.user_app,
            app_secret=request.json.app_secret,
        )

    @analyse.json(Validator('mark', '应用评分').to(int))
    @analyse.argument(AppParams.user_app)
    @Auth.require_login(deny_auth_token=True)
    def put(self, request, **kwargs):
        """ PUT /api/app/user/:user_app_id

        给app评分
        """
        return AppService.update_user_mark(
            user=request.user,
            user_app=request.argument.user_app,
            mark=request.json.mark,
        )


class FrequencyRefreshView(View):
    def get(self, request):
        """ GET /api/app/refresh-frequent-score

        更新用户应用的使用频率度，判断是否为常用应用
        """
        return AppService.refresh_frequency_scores()


class UserNumView(View):
    def get(self, request):
        return AppService.fix_user_numbers()
