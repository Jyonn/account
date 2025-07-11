import datetime

from diq import Dictify
from django.db import models
from django.utils.crypto import get_random_string
from smartdjango import OK, Error

from App.validators import AppErrors, PremiseValidator, ScopeValidator, AppValidator, UserAppValidator
from Base.jtoken import JWType, JWT
from Base.premise_checker import PremiseCheckerErrors
from Config.models import CI


class Premise(models.Model, Dictify):
    vldt = PremiseValidator

    """要求类，不满足要求无法进入应用"""
    name = models.CharField(
        verbose_name='要求英文简短名称',
        max_length=vldt.MAX_NAME_LENGTH,
        unique=True,
    )
    desc = models.CharField(
        verbose_name='要求介绍',
        max_length=vldt.MAX_DESC_LENGTH,
    )
    detail = models.CharField(
        verbose_name='要求详细说明',
        max_length=vldt.MAX_DETAIL_LENGTH,
        default=None,
    )

    @classmethod
    def get_by_id(cls, pid):
        try:
            return cls.objects.get(pk=pid)
        except cls.DoesNotExist:
            raise AppErrors.PREMISE_NOT_FOUND

    @classmethod
    def get_by_name(cls, name):
        try:
            return cls.objects.get(name=name)
        except Exception as err:
            raise AppErrors.PREMISE_NOT_FOUND(details=err)

    @classmethod
    def create(cls, name, desc, detail):
        try:
            premise = cls(
                name=name,
                desc=desc,
                detail=detail,
            )
            premise.save()
        except Exception as err:
            raise AppErrors.CREATE_PREMISE(details=err)
        return premise

    def d(self):
        return self.dictify('name', 'desc', 'detail')

    @classmethod
    def list_to_premise_list(cls, premises):
        premise_list = []
        if not isinstance(premises, list):
            return []
        for premise_name in premises:
            try:
                premise_list.append(cls.get_by_name(premise_name))
            except Exception:
                pass
        return premise_list

    @staticmethod
    def get_checker(p_name):
        c_name = p_name[0]
        for i in range(1, len(p_name)):
            if p_name[i].isupper() and not p_name[i - 1].isupper():
                c_name += '_'
                c_name += p_name[i]
            elif p_name[i].isupper() and p_name[i - 1].isupper() and p_name[i + 1].islower():
                c_name += '_'
                c_name += p_name[i]
            else:
                c_name += p_name[i]
        checker_name = c_name.lower() + '_checker'

        from Base.premise_checker import PremiseChecker
        return getattr(PremiseChecker, checker_name, None)


class Scope(models.Model, Dictify):
    vldt = ScopeValidator

    """权限类"""
    name = models.CharField(
        verbose_name='权限英文简短名称',
        max_length=vldt.MAX_NAME_LENGTH,
        unique=True,
    )
    desc = models.CharField(
        verbose_name='权限介绍',
        max_length=vldt.MAX_DESC_LENGTH,
    )
    always = models.BooleanField(
        null=True,
        blank=True,
        verbose_name="Null 可有可无 True 一直可选 False 一直不可选",
        default=None,
    )
    detail = models.CharField(
        verbose_name='权限详细说明',
        max_length=vldt.MAX_DETAIL_LENGTH,
        default=None,
    )

    @classmethod
    def get_by_id(cls, sid):
        try:
            return cls.objects.get(pk=sid)
        except cls.DoesNotExist:
            raise AppErrors.SCOPE_NOT_FOUND

    @classmethod
    def get_by_name(cls, name):
        try:
            return cls.objects.get(name=name)
        except Exception:
            raise AppErrors.SCOPE_NOT_FOUND

    @classmethod
    def create(cls, name, desc, detail):
        try:
            scope = cls(
                name=name,
                desc=desc,
                detail=detail,
                always=None,
            )
            scope.save()
        except Exception:
            raise AppErrors.CREATE_SCOPE
        return scope

    def d(self):
        return self.dictify('name', 'desc', 'always', 'detail')

    @classmethod
    def list_to_scope_list(cls, scopes):
        scope_list = []
        if not isinstance(scopes, list):
            return []
        for scope_name in scopes:
            try:
                scope = cls.get_by_name(scope_name)
                if scope.always is not False:  # 此处不能将 != False 删除 因为要考虑None的情况
                    scope_list.append(scope)
            except Exception:
                pass

        # 仍然存在always是True的但没有被添加的情况 于是double_check
        return cls.double_check(scope_list)

    @classmethod
    def double_check(cls, scope_list):
        final_list = []
        for scope in cls.objects.all():
            if scope.always:
                final_list.append(scope)
        for scope in scope_list:
            if scope.always is None:  # false被忽略，true已经添加
                final_list.append(scope)
        return final_list


class App(models.Model, Dictify):
    vldt = AppValidator

    R_USER = 'user'
    R_OWNER = 'owner'
    R_NONE = 'none'
    R_LIST = [R_USER, R_OWNER, R_NONE]

    name = models.CharField(
        verbose_name='应用名称',
        max_length=vldt.MAX_NAME_LENGTH,
        unique=True,
        validators=[vldt.name]
    )
    id = models.CharField(
        verbose_name='应用唯一ID',
        max_length=vldt.MAX_ID_LENGTH,
        primary_key=True,
    )
    secret = models.CharField(
        verbose_name='应用密钥',
        max_length=vldt.MAX_SECRET_LENGTH,
    )
    redirect_uri = models.URLField(
        verbose_name='应用跳转URI',
        max_length=vldt.MAX_REDIRECT_URI_LENGTH,
    )
    test_redirect_uri = models.URLField(
        verbose_name='测试环境下的应用跳转URI',
        max_length=vldt.MAX_TEST_REDIRECT_URI_LENGTH,
        default=None,
    )
    scopes = models.ManyToManyField(
        'Scope',
        default=None,
    )
    premises = models.ManyToManyField(
        'Premise',
        default=None,
    )
    owner = models.ForeignKey(
        'User.User',
        on_delete=models.CASCADE,
        db_index=True,
    )
    field_change_time = models.FloatField(
        null=True,
        blank=True,
        default=0,
    )
    desc = models.CharField(
        max_length=vldt.MAX_DESC_LENGTH,
        default=None,
    )
    logo = models.CharField(
        default=None,
        null=True,
        blank=True,
        max_length=vldt.MAX_LOGO_LENGTH,
    )
    mark = models.SlugField(
        default='0-0-0-0-0',
        verbose_name='1-5分评分人数',
    )
    info = models.TextField(
        default=None,
        verbose_name='应用介绍信息',
        null=True,
    )
    user_num = models.IntegerField(
        default=0,
        verbose_name='用户人数',
    )
    create_time = models.DateTimeField(
        default=None,
    )
    max_user_num = models.IntegerField(
        default=0,
        verbose_name='最多注册用户'
    )

    @classmethod
    def get_by_name(cls, name):
        try:
            return cls.objects.get(name=name)
        except cls.DoesNotExist:
            raise AppErrors.APP_NOT_FOUND

    @classmethod
    def exist_with_name(cls, name):
        try:
            cls.objects.get(name=name)
        except cls.DoesNotExist:
            return
        raise AppErrors.EXIST_APP_NAME

    @classmethod
    def get_by_id(cls, app_id):
        try:
            return cls.objects.get(pk=app_id)
        except cls.DoesNotExist:
            raise AppErrors.APP_NOT_FOUND

    @classmethod
    def get_unique_app_id(cls):
        while True:
            app_id = get_random_string(length=cls.vldt.DEFAULT_ID_LENGTH)
            try:
                cls.get_by_id(app_id)
            except AppErrors.APP_NOT_FOUND:
                return app_id

    @classmethod
    def create(cls, name, desc, redirect_uri, test_redirect_uri, scopes, premises, owner):
        cls.exist_with_name(name)

        try:
            crt_time = datetime.datetime.now()
            app = cls(
                name=name,
                desc=desc,
                id=cls.get_unique_app_id(),
                secret=get_random_string(length=cls.vldt.MAX_SECRET_LENGTH),
                redirect_uri=redirect_uri,
                test_redirect_uri=test_redirect_uri,
                owner=owner,
                field_change_time=datetime.datetime.now().timestamp(),
                info=None,
                create_time=crt_time,
            )
            app.save()
            app.scopes.add(*scopes)
            app.premises.add(*premises)
            app.save()
        except Exception as err:
            raise AppErrors.CREATE_APP(details=err)
        return app

    def modify_test_redirect_uri(self, test_redirect_uri):
        self.test_redirect_uri = test_redirect_uri
        self.save()

    def modify(self, name, desc, info, redirect_uri, scopes, premises, max_user_num):
        """修改应用信息"""
        self.name = name
        self.desc = desc
        self.info = info
        self.redirect_uri = redirect_uri
        self.max_user_num = max_user_num
        for scope in self.scopes.all():
            self.scopes.remove(scope)
        self.scopes.add(*scopes)
        for premise in self.premises.all():
            self.premises.remove(premise)
        self.premises.add(*premises)
        self.field_change_time = datetime.datetime.now().timestamp()
        try:
            self.save()
        except Exception as err:
            raise AppErrors.MODIFY_APP(details=err)

    def _dictify_app_name(self):
        return self.name

    def _dictify_app_id(self):
        return self.id

    def _dictify_app_desc(self):
        return self.desc

    def _dictify_logo(self, small=True):
        if self.logo is None:
            return None
        from Base.qn import qn_public_manager
        key = "%s-small" % self.logo if small else self.logo
        return qn_public_manager.get_resource_url(key)

    def _dictify_create_time(self):
        return self.create_time.timestamp()

    def _dictify_app_info(self):
        return self.info

    def _dictify_owner(self):
        return self.owner.d_base()

    def _dictify_mark(self):
        return list(map(int, self.mark.split('-')))

    def mark_as_list(self):
        return self._dictify_mark()

    def _dictify_scopes(self):
        scopes = self.scopes.all()
        return list(map(lambda s: s.d(), scopes))

    def _dictify_premises(self):
        premises = self.premises.all()
        return list(map(lambda p: p.d(), premises))

    def d(self):
        return self.dictify(
            'app_name', 'app_id', 'app_desc', 'app_info', 'user_num', ('logo', False),
            'redirect_uri', 'create_time', 'owner', 'mark', 'scopes', 'premises',
            'test_redirect_uri', 'max_user_num')

    def d_user(self, user):
        dict_ = self.d()
        dict_.update(dict(premises=self.check_premise(user)))
        return dict_

    def d_base(self):
        return self.dictify('app_name', 'app_id', 'logo', 'app_desc', 'user_num', 'create_time')

    def modify_logo(self, logo):
        """修改应用logo"""
        from Base.qn import qn_public_manager
        if self.logo:
            qn_public_manager.delete_res(self.logo)
        self.logo = logo
        self.save()

    def is_user_full(self):
        if self.max_user_num == 0:
            return False
        return self.max_user_num < self.user_num

    def belong(self, user):
        return self.owner == user

    def authentication(self, app_secret):
        return self.secret == app_secret

    def check_premise(self, user):
        premises = []
        for premise in self.premises.all():
            checker = Premise.get_checker(premise.name)
            if checker and callable(checker):
                try:
                    checker(user)
                    raise OK
                except Error as e:
                    error = e
            else:
                error = PremiseCheckerErrors.CHECKER_NOT_FOUND
            p_dict = premise.d()
            p_dict['check'] = dict(
                identifier=error.identifier,
                msg=error.message,
            )
            premises.append(p_dict)
        return premises

    @classmethod
    def list(cls):
        # return cls.objects.all().dict(cls.d_base)
        apps = cls.objects.all()
        return [app.d_base() for app in apps]


class UserApp(models.Model, Dictify):
    vldt = UserAppValidator

    """用户应用类"""
    user = models.ForeignKey(
        'User.User',
        on_delete=models.CASCADE,
    )
    app = models.ForeignKey(
        'App.App',
        on_delete=models.CASCADE,
    )
    user_app_id = models.CharField(
        max_length=vldt.MAX_USER_APP_ID_LENGTH,
        verbose_name='用户在这个app下的唯一ID',
        unique=True,
    )
    bind = models.BooleanField(
        default=False,
        verbose_name='用户是否绑定应用',
    )
    last_auth_code_time = models.CharField(
        default=None,
        verbose_name='上一次申请auth_code的时间，防止被多次使用',
        max_length=vldt.MAX_LAST_USER_APP_ID_LENGTH,
    )
    frequent_score = models.FloatField(
        verbose_name='频繁访问分数，按分值排序为常用应用',
        default=0,
    )
    last_score_changed_time = models.CharField(
        default=None,
        verbose_name='上一次分数变化的时间',
        max_length=vldt.MAX_LAST_SCORE_CHANGED_TIME_LENGTH,
    )
    mark = models.PositiveSmallIntegerField(
        verbose_name='此用户的打分，0表示没打分',
        default=0,
    )

    def _dictify_rebind(self):
        return float(self.last_auth_code_time) < self.app.field_change_time

    def d(self):
        return self.dictify('bind', 'mark', 'rebind', 'user_app_id')

    @classmethod
    def get_by_user_app(cls, user, app):
        try:
            return cls.objects.get(user=user, app=app)
        except Exception:
            raise AppErrors.USER_APP_NOT_FOUND

    @classmethod
    def get_by_id(cls, user_app_id, check_bind=False):
        try:
            user_app = cls.objects.get(user_app_id=user_app_id)
        except Exception:
            raise AppErrors.USER_APP_NOT_FOUND
        if check_bind and not user_app.bind:
            raise AppErrors.APP_NOT_BOUND
        return user_app

    @classmethod
    def get_unique_id(cls):
        while True:
            user_app_id = get_random_string(length=8)
            try:
                cls.get_by_id(user_app_id)
            except AppErrors.USER_APP_NOT_FOUND:
                return user_app_id

    @classmethod
    def do_bind(cls, user, app):
        if app.is_user_full():
            raise AppErrors.USER_FULL

        premise_list = app.check_premise(user)
        for premise in premise_list:
            error = E.sid2e[premise['check']['identifier']]
            if not error.ok:
                raise error

        crt_timestamp = datetime.datetime.now().timestamp()

        try:
            user_app = cls.get_by_user_app(user, app)
            user_app.bind = True
            user_app.last_auth_code_time = crt_timestamp
            user_app.frequent_score += 1
            user_app.last_score_changed_time = crt_timestamp
            user_app.save()
        except AppErrors.USER_APP_NOT_FOUND:
            try:
                user_app = cls(
                    user=user,
                    app=app,
                    user_app_id=cls.get_unique_id(),
                    bind=True,
                    last_auth_code_time=crt_timestamp,
                    frequent_score=1,
                    last_score_changed_time=crt_timestamp,
                )
                user_app.save()
                user_app.app.user_num += 1
                user_app.app.save()
            except Exception as err:
                raise AppErrors.BIND_USER_APP(details=err)
        return JWT.encrypt(dict(
            user_app_id=user_app.user_app_id,
            type=JWType.AUTH_CODE,
            ctime=crt_timestamp
        ), replace=False, expire_second=5 * 60)

    @classmethod
    def check_bind(cls, user, app):
        try:
            user_app = cls.get_by_user_app(user, app)
            return user_app.bind
        except Exception:
            return False

    @classmethod
    def refresh_frequent_score(cls):
        from Config.models import Config
        crt_date = datetime.datetime.now().date()
        crt_time = datetime.datetime.now().timestamp()
        last_date = Config.get_value_by_key(CI.LAST_RE_FREQ_SCORE_DATE)
        last_date = datetime.datetime.strptime(last_date, '%Y-%m-%d').date()

        if last_date >= crt_date:
            raise AppErrors.SCORE_REFRESHED

        from OAuth.views import OAUTH_TOKEN_EXPIRE_TIME

        Config.update_value(CI.LAST_RE_FREQ_SCORE_DATE, crt_date.strftime('%Y-%m-%d'))
        for user_app in cls.objects.all():
            if crt_time - float(
                    user_app.last_auth_code_time) > OAUTH_TOKEN_EXPIRE_TIME + 24 * 60 * 60:
                if crt_time - float(user_app.last_score_changed_time) > OAUTH_TOKEN_EXPIRE_TIME:
                    user_app.frequent_score /= 2
                    user_app.last_score_changed_time = crt_time
                    user_app.save()

    def do_mark(self, mark):
        if mark < 1 or mark > 5:
            raise AppErrors.MARK
        original_mark = self.mark
        self.mark = mark
        self.save()

        mark_list = list(map(int, self.app.mark.split('-')))
        if 5 >= original_mark > 0:
            mark_list[original_mark - 1] -= 1
        mark_list[mark - 1] += 1
        self.app.mark = '-'.join(map(str, mark_list))
        self.app.save()

#
# class AppP:
#     name, info, desc, redirect_uri, test_redirect_uri, secret, max_user_num = App.P(
#         'name', 'info', 'desc', 'redirect_uri', 'test_redirect_uri', 'secret', 'max_user_num')
#     scopes = P('scopes', '应用权限列表').process(Scope.list_to_scope_list)
#     premises = P('premises', '应用要求列表').process(Premise.list_to_premise_list)
#
#     app = P('app_id', '应用ID', 'app').process(App.get_by_id)
#     user_app = P('user_app_id', '用户绑定应用ID', 'user_app').process(UserApp.get_by_id)
