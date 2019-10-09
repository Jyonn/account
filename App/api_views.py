import datetime

from SmartDjango import P, Analyse
from SmartDjango.models import Pager, Page
from django.views import View

from App.models import App, Scope, UserApp, Premise, AppError, AppP
from Base.auth import Auth
from Base.policy import Policy
from Base.qn import qn_public_manager
from Base.scope import SI
from User.models import User


def relation_process(relation):
    if relation not in App.R_LIST:
        relation = App.R_USER
    return relation


class AppView(View):
    @staticmethod
    @Analyse.r(q=[
        P('relation').set_default(App.R_USER).process(relation_process),
        P('frequent').set_null(),
        P('count').set_default(3).process(int),
        P('last_time').set_null().process(float).process(datetime.datetime.fromtimestamp)
    ])
    @Auth.require_login([SI.read_app_list])
    def get(r):
        """ GET /api/app/

        获取与我相关的app列表
        """
        user = r.user
        relation = r.d.relation

        if relation == App.R_OWNER:
            return App.objects.filter(owner=user).dict(App.d_base)
        elif relation == App.R_NONE:
            count = r.d.count
            last_time = r.d.last_time
            pager = Pager(compare_field='create_time')
            page = App.objects.page(pager, last_time, count)  # type: Page
            return page.object_list.dict(App.d_base)
        else:
            frequent = r.d.frequent
            count = r.d.count
            objects = UserApp.objects.filter(user=user, bind=True)
            if frequent:
                pager = Pager(mode=Pager.CHOOSE_AMONG, order_by=('-frequent_score', ))
                objects = objects.page(pager, 0, count).object_list
            return list(map(lambda o: o.app.d_base(), objects))

    @staticmethod
    @Analyse.r([AppP.name, AppP.desc, AppP.redirect_uri, AppP.test_redirect_uri,
                AppP.scopes, AppP.premises])
    @Auth.require_login(deny_auth_token=True)
    def post(r):
        """ POST /api/app/

        创建我的app
        """
        app = App.create(owner=r.user, **r.d.dict())
        return app.d_base()


class AppIDSecretView(View):
    @staticmethod
    @Analyse.r(a=[AppP.app])
    @Auth.require_login(deny_auth_token=True)
    def get(r):
        """ GET /api/app/:app_id/secret"""
        user = r.user
        app = r.d.app

        if not app.belong(user):
            return AppError.APP_NOT_BELONG

        return app.secret


class AppIDView(View):
    @staticmethod
    @Analyse.r(a=[AppP.app])
    @Auth.require_login(deny_auth_token=True, allow_no_login=True)
    def get(r):
        """ GET /api/app/:app_id

        获取应用信息以及用户与应用的关系（属于、绑定、打分，仅限用户登录时）
        """
        user = r.user
        app = r.d.app

        dict_ = app.d_user(user)

        try:
            user_app = UserApp.get_by_user_app(user, app)
            relation = user_app.d()
        except Exception:
            relation = dict(bind=False, rebind=False, mark=0, belong=False, user_app_id=None)

        relation['belong'] = app.belong(user)
        dict_['relation'] = relation

        return dict_

    @staticmethod
    @Analyse.r(
        b=[
            AppP.name.clone().set_null(),
            AppP.info.clone().set_null(),
            AppP.desc.clone().set_null(),
            AppP.redirect_uri.clone().set_null(),
            AppP.scopes.clone().set_null(),
            AppP.premises.clone().set_null(),
            AppP.test_redirect_uri.clone().set_null(),
        ],
        a=[AppP.app],
    )
    @Auth.require_login(deny_auth_token=True)
    def put(r):
        """ PUT /api/app/:app_id

        修改应用信息
        """
        user = r.user
        app = r.d.app

        if not app.belong(user):
            return AppError.APP_NOT_BELONG

        app.modify(**r.d.dict('name', 'desc', 'info', 'redirect_uri', 'scopes', 'premises'))
        app.modify_test_redirect_uri(r.d.test_redirect_uri)
        return app.d_user(user)

    @staticmethod
    @Analyse.r(a=[AppP.app])
    @Auth.require_login(deny_auth_token=True)
    def delete(r):
        """ DELETE /api/app/:app_id

        删除应用
        """
        app = r.user
        app = r.d.app

        if not app.belong(app):
            return AppError.APP_NOT_BELONG

        app.delete()


class ScopeView(View):
    @staticmethod
    def get(r):
        return Scope.objects.dict(Scope.d)


class PremiseView(View):
    @staticmethod
    def get(r):
        return Premise.objects.dict(Premise.d)


class AppLogoView(View):
    @staticmethod
    @Analyse.r(q=[P('filename', '文件名'), AppP.app])
    @Auth.require_login(deny_auth_token=True)
    def get(r):
        """ GET /api/app/logo

        获取七牛上传token
        """
        user = r.user

        filename = r.d.filename
        app = r.d.app  # type: App

        if app.owner != user:
            return AppError.APP_NOT_BELONG

        import datetime
        crt_time = datetime.datetime.now().timestamp()
        key = 'app/%s/logo/%s/%s' % (app.id, crt_time, filename)
        qn_token, key = qn_public_manager.get_upload_token(key, Policy.logo(app.id))
        return dict(upload_token=qn_token, key=key)

    @staticmethod
    @Analyse.r([P('key', '七牛存储键'), AppP.app])
    def post(r):
        """ POST /api/app/logo

        七牛上传应用logo回调函数
        """
        qn_public_manager.qiniu_auth_callback(r)

        key = r.d.key
        app = r.d.app
        app.modify_logo(key)
        return app.d()


class UserAppIdView(View):
    @staticmethod
    @Analyse.r(b=[AppP.secret.clone().rename('app_secret')], a=[AppP.user_app])
    def post(r):
        """ POST /api/app/user/:user_app_id

        通过app获取user信息
        """

        app_secret = r.d.app_secret
        user_app = r.d.user_app

        if not user_app.app.authentication(app_secret):
            return AppError.APP_SECRET

        return user_app.user.d()

    @staticmethod
    @Analyse.r(b=[P('mark', '应用评分').process(int)], a=[AppP.user_app])
    @Auth.require_login(deny_auth_token=True)
    def put(r):
        """ PUT /api/app/user/:user_app_id

        给app评分
        """
        user_app = r.d.user_app
        mark = r.d.mark
        if user_app.user.user_str_id != r.user.user_str_id:
            return AppError.ILLEGAL_ACCESS_RIGHT

        user_app.do_mark(mark)
        return user_app.app.mark_as_list()


@Analyse.r(method='GET')
def refresh_frequent_score(r):
    """ GET /api/app/refresh-frequent-score

    更新用户应用的使用频率度，判断是否为常用应用
    """
    UserApp.refresh_frequent_score()


@Analyse.r(method='GET')
def shorten_app_id(r):
    for app in App.objects.all():
        app.id = app.id[:8]
        app.save()
