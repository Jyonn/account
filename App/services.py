import datetime

from smartdjango import OK

from App.models import App, UserApp
from App.validators import AppErrors
from Base.policy import Policy
from Base.qn import qn_public_manager


class AppService:
    @staticmethod
    def list_related_apps(user, relation, frequent=None, count=3, last_time=None):
        if relation == App.R_OWNER:
            apps = App.objects.filter(owner=user)
            return [app.d_base() for app in apps]

        if relation == App.R_NONE:
            apps = App.objects.all()
            if last_time is not None:
                apps = apps.filter(create_time__gt=last_time)
            apps = apps.order_by('create_time')[:count]
            return [app.d_base() for app in apps]

        apps = UserApp.objects.filter(user=user, bind=True)
        if frequent:
            apps = apps.order_by('-frequent_score')[:count]
        return [user_app.app.d_base() for user_app in apps]

    @staticmethod
    def create_app(owner, payload):
        app = App.create(owner=owner, **payload)
        return app.d_base()

    @staticmethod
    def get_secret(user, app):
        AppService.ensure_belong(user, app)
        return app.secret

    @staticmethod
    def get_detail(user, app):
        app_dict = app.d_user(user) if user else app.d()

        try:
            user_app = UserApp.get_by_user_app(user, app)
            relation = user_app.d()
        except Exception:
            relation = dict(bind=False, rebind=False, mark=0, belong=False, user_app_id=None)

        relation['belong'] = app.belong(user)
        app_dict['relation'] = relation
        return app_dict

    @staticmethod
    def update_app(user, app, payload):
        AppService.ensure_belong(user, app)
        app.modify(
            name=payload['name'],
            desc=payload['desc'],
            info=payload['info'],
            redirect_uri=payload['redirect_uri'],
            scopes=payload['scopes'],
            premises=payload['premises'],
            max_user_num=payload['max_user_num'],
        )
        app.modify_test_redirect_uri(payload['test_redirect_uri'])
        return app.d_user(user)

    @staticmethod
    def delete_app(user, app):
        AppService.ensure_belong(user, app)
        app.delete()
        return OK

    @staticmethod
    def get_logo_upload_token(user, filename, app):
        AppService.ensure_belong(user, app)
        crt_time = datetime.datetime.now().timestamp()
        key = 'app/%s/logo/%s/%s' % (app.id, crt_time, filename)
        qn_token, key = qn_public_manager.get_upload_token(key, Policy.logo(app.id))
        return dict(upload_token=qn_token, key=key)

    @staticmethod
    def handle_logo_uploaded(app, key):
        app.modify_logo(key)
        return app.d()

    @staticmethod
    def authenticate_user_app(user_app, app_secret):
        if not user_app.app.authentication(app_secret):
            raise AppErrors.APP_SECRET
        return user_app.user.d()

    @staticmethod
    def update_user_mark(user, user_app, mark):
        if user_app.user.user_str_id != user.user_str_id:
            raise AppErrors.ILLEGAL_ACCESS_RIGHT
        user_app.do_mark(mark)
        return user_app.app.mark_as_list()

    @staticmethod
    def refresh_frequency_scores():
        UserApp.refresh_frequent_score()
        return OK

    @staticmethod
    def fix_user_numbers():
        for app in App.objects.all():
            app.user_num = app.userapp_set.count()
            app.save()
        return OK

    @staticmethod
    def ensure_belong(user, app):
        if not app.belong(user):
            raise AppErrors.APP_NOT_BELONG
