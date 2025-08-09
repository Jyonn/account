import datetime

from django.views import View
from smartdjango import analyse, Validator, OK

from App.models import App, Scope, UserApp, Premise
from App.params import AppParams
from App.validators import AppErrors
from Base.auth import Auth
from Base.policy import Policy
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
        user = request.user
        relation = request.query.relation

        if relation == App.R_OWNER:
            apps = App.objects.filter(owner=user)
            return [app.d_base() for app in apps]
        elif relation == App.R_NONE:
            count = request.query.count
            last_time = request.query.last_time
            apps = App.objects.filter(create_time__gt=last_time).order_by('create_time')[:count]
            return [app.d_base() for app in apps]
        else:
            frequent = request.query.frequent
            count = request.query.count
            apps = UserApp.objects.filter(user=user, bind=True)

            if frequent:
                apps = apps.order_by('-frequent_score')[:count]
            # return list(map(lambda o: o.app.d_base(), apps))
            return [app.app.d_base() for app in apps]

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
        app = App.create(owner=request.user, **request.json())
        return app.d_base()


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
        user = request.user
        app = request.argument.app

        if not app.belong(user):
            raise AppErrors.APP_NOT_BELONG

        return app.secret


class AppID(View):
    @analyse.argument(AppParams.app)
    @Auth.require_login(deny_auth_token=True, allow_no_login=True)
    def get(self, request, **kwargs):
        """ GET /api/app/:app_id

        获取应用信息以及用户与应用的关系（属于、绑定、打分，仅限用户登录时）
        """
        user = request.user
        app = request.argument.app

        if user:
            dict_ = app.d_user(user)
        else:
            dict_ = app.d()

        try:
            user_app = UserApp.get_by_user_app(user, app)
            relation = user_app.d()
        except Exception:
            relation = dict(bind=False, rebind=False, mark=0, belong=False, user_app_id=None)

        relation['belong'] = app.belong(user)
        dict_['relation'] = relation

        return dict_

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
        user = request.user
        app = request.argument.app

        if not app.belong(user):
            raise AppErrors.APP_NOT_BELONG

        app.modify(
            name=request.json.name,
            desc=request.json.desc,
            info=request.json.info,
            redirect_uri=request.json.redirect_uri,
            scopes=request.json.scopes,
            premises=request.json.premises,
            max_user_num=request.json.max_user_num
        )
        app.modify_test_redirect_uri(request.json.test_redirect_uri)
        return app.d_user(user)

    @analyse.argument(AppParams.app)
    @Auth.require_login(deny_auth_token=True)
    def delete(self, request, **kwargs):
        """ DELETE /api/app/:app_id

        删除应用
        """
        app = request.user
        app = request.argument.app

        if not app.belong(app):
            raise AppErrors.APP_NOT_BELONG

        app.delete()


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
        user = request.user

        filename = request.query.filename
        app = request.query.app  # type: App

        if app.owner != user:
            raise AppErrors.APP_NOT_BELONG

        crt_time = datetime.datetime.now().timestamp()
        key = 'app/%s/logo/%s/%s' % (app.id, crt_time, filename)
        qn_token, key = qn_public_manager.get_upload_token(key, Policy.logo(app.id))
        return dict(upload_token=qn_token, key=key)

    @analyse.json(Validator('key', '七牛存储键'), AppParams.app)
    def post(self, request):
        """ POST /api/app/logo

        七牛上传应用logo回调函数
        """
        qn_public_manager.auth_callback(self, request)

        key = request.json.key
        app = request.json.app
        app.modify_logo(key)
        return app.d()


class UserAppIdView(View):
    @analyse.json(AppParams.secret.copy().rename('app_secret'))
    @analyse.argument(AppParams.user_app)
    def post(self, request, **kwargs):
        """ POST /api/app/user/:user_app_id

        通过app获取user信息
        """

        app_secret = request.json.app_secret
        user_app = request.argument.user_app

        if not user_app.app.authentication(app_secret):
            raise AppErrors.APP_SECRET

        return user_app.user.d()

    @analyse.json(Validator('mark', '应用评分').to(int))
    @analyse.argument(AppParams.user_app)
    @Auth.require_login(deny_auth_token=True)
    def put(self, request, **kwargs):
        """ PUT /api/app/user/:user_app_id

        给app评分
        """
        user_app = request.argument.user_app
        mark = request.json.mark
        if user_app.user.user_str_id != request.user.user_str_id:
            raise AppErrors.ILLEGAL_ACCESS_RIGHT

        user_app.do_mark(mark)
        return user_app.app.mark_as_list()


class FrequencyRefreshView(View):
    def get(self, request):
        """ GET /api/app/refresh-frequent-score

        更新用户应用的使用频率度，判断是否为常用应用
        """
        UserApp.refresh_frequent_score()
        return OK


class UserNumView(View):
    def get(self, request):
        for app in App.objects.all():
            app.user_num = app.userapp_set.count()
            app.save()
        return OK
