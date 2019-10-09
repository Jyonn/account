import datetime

from SmartDjango import models, E, Excp, BaseError, P, ErrorJar
from django.utils.crypto import get_random_string

from Base.jtoken import JWType, JWT
from Base.premise_checker import PremiseCheckerError
from Config.models import CI


@E.register
class AppError:
    PREMISE_NOT_FOUND = E("不存在的要求")
    CREATE_PREMISE = E("创建要求错误")

    CREATE_SCOPE = E("创建权限错误")
    SCOPE_NOT_FOUND = E("不存在的权限")

    APP_NOT_FOUND = E("不存在的应用")
    CREATE_APP = E("创建应用错误")
    EXIST_APP_NAME = E("已存在此应用名")
    APP_NOT_BELONG = E("不是你的应用")
    MODIFY_APP = E("修改应用信息错误")

    USER_APP_NOT_FOUND = E("请仔细阅读应用所需权限")
    BIND_USER_APP = E("无法绑定应用")
    APP_UNBINDED = E("应用被用户解绑")

    SCORE_REFRESHED = E("频率分数已经刷新")

    MARK = E("评分失败")
    APP_SECRET = E("错误的应用密钥")

    ILLEGAL_ACCESS_RIGHT = E("非法访问权限")


class Premise(models.Model):
    """要求类，不满足要求无法进入应用"""
    name = models.CharField(
        verbose_name='要求英文简短名称',
        max_length=20,
        unique=True,
    )
    desc = models.CharField(
        verbose_name='要求介绍',
        max_length=20,
    )
    detail = models.CharField(
        verbose_name='要求详细说明',
        max_length=100,
        default=None,
    )

    @classmethod
    @Excp.pack
    def get_by_id(cls, pid):
        try:
            return cls.objects.get(pk=pid)
        except cls.DoesNotExist:
            return AppError.PREMISE_NOT_FOUND

    @classmethod
    @Excp.pack
    def get_by_name(cls, name):
        try:
            return cls.objects.get(name=name)
        except Exception:
            return AppError.PREMISE_NOT_FOUND

    @classmethod
    @Excp.pack
    def create(cls, name, desc, detail):
        try:
            premise = cls(
                name=name,
                desc=desc,
                detail=detail,
            )
            premise.save()
        except Exception:
            return AppError.CREATE_PREMISE
        return premise

    def d(self):
        return self.dictor('name', 'desc', 'detail')

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


class Scope(models.Model):
    """权限类"""
    name = models.CharField(
        verbose_name='权限英文简短名称',
        max_length=20,
        unique=True,
    )
    desc = models.CharField(
        verbose_name='权限介绍',
        max_length=20,
    )
    always = models.NullBooleanField(
        verbose_name="Null 可有可无 True 一直可选 False 一直不可选",
        default=None,
    )
    detail = models.CharField(
        verbose_name='权限详细说明',
        max_length=100,
        default=None,
    )

    @classmethod
    @Excp.pack
    def get_by_id(cls, sid):
        try:
            return cls.objects.get(pk=sid)
        except cls.DoesNotExist:
            return AppError.SCOPE_NOT_FOUND

    @classmethod
    @Excp.pack
    def get_by_name(cls, name):
        try:
            return cls.objects.get(name=name)
        except Exception:
            return AppError.SCOPE_NOT_FOUND

    @classmethod
    @Excp.pack
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
            return AppError.CREATE_SCOPE
        return scope

    def d(self):
        return self.dictor('name', 'desc', 'always', 'detail')

    @classmethod
    def list_to_scope_list(cls, scopes):
        scope_list = []
        if not isinstance(scopes, list):
            return []
        for scope_name in scopes:
            try:
                scope = cls.get_by_name(scope_name)
                if scope.always != False:  # 此处不能将 != False 删除 因为要考虑None的情况
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


class App(models.Model):
    R_USER = 'user'
    R_OWNER = 'owner'
    R_NONE = 'none'
    R_LIST = [R_USER, R_OWNER, R_NONE]

    name = models.CharField(
        verbose_name='应用名称',
        max_length=32,
        min_length=2,
        unique=True,
    )
    id = models.CharField(
        verbose_name='应用唯一ID',
        max_length=32,
        primary_key=True,
    )
    secret = models.CharField(
        verbose_name='应用密钥',
        max_length=32,
    )
    redirect_uri = models.URLField(
        verbose_name='应用跳转URI',
        max_length=512,
    )
    test_redirect_uri = models.URLField(
        verbose_name='测试环境下的应用跳转URI',
        max_length=512,
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
        max_length=32,
        default=None,
    )
    logo = models.CharField(
        default=None,
        null=True,
        blank=True,
        max_length=1024,
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

    @classmethod
    @Excp.pack
    def get_by_name(cls, name):
        try:
            return cls.objects.get(name=name)
        except cls.DoesNotExist:
            return AppError.APP_NOT_FOUND

    @classmethod
    @Excp.pack
    def get_by_id(cls, app_id):
        try:
            return cls.objects.get(pk=app_id)
        except cls.DoesNotExist:
            return AppError.APP_NOT_FOUND

    @classmethod
    def get_unique_app_id(cls):
        while True:
            app_id = get_random_string(length=8)
            try:
                cls.get_by_id(app_id)
            except Excp as ret:
                if ret.eis(AppError.APP_NOT_FOUND):
                    return app_id

    @classmethod
    @Excp.pack
    def create(cls, name, desc, redirect_uri, test_redirect_uri, scopes, premises, owner):
        try:
            cls.get_by_name(name)
            return AppError.EXIST_APP_NAME
        except Excp:
            pass

        try:
            crt_time = datetime.datetime.now()
            app = cls(
                name=name,
                desc=desc,
                id=cls.get_unique_app_id(),
                secret=get_random_string(length=32),
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
        except Exception:
            return AppError.CREATE_APP
        return app

    def modify_test_redirect_uri(self, test_redirect_uri):
        self.test_redirect_uri = test_redirect_uri
        self.save()

    @Excp.pack
    def modify(self, name, desc, info, redirect_uri, scopes, premises):
        """修改应用信息"""
        self.name = name
        self.desc = desc
        self.info = info
        self.redirect_uri = redirect_uri
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
            print(err)
            return AppError.MODIFY_APP

    def _readable_app_name(self):
        return self.name

    def _readable_app_id(self):
        return self.id

    def _readable_app_desc(self):
        return self.desc

    def _readable_logo(self, small=True):
        if self.logo is None:
            return None
        from Base.qn import qn_public_manager
        key = "%s-small" % self.logo if small else self.logo
        return qn_public_manager.get_resource_url(key)

    def _readable_create_time(self):
        return self.create_time.timestamp()

    def _readable_app_info(self):
        return self.info

    def _readable_owner(self):
        return self.owner.d_base()

    def _readable_mark(self):
        return list(map(int, self.mark.split('-')))

    def mark_as_list(self):
        return self._readable_mark()

    def _readable_scopes(self):
        scopes = self.scopes.all()
        return list(map(lambda s: s.d(), scopes))

    def _readable_premises(self):
        premises = self.premises.all()
        return list(map(lambda p: p.d(), premises))

    def d(self):
        return self.dictor(
            'app_name', 'app_id', 'app_desc', 'app_info', 'user_num', ('logo', False),
            'redirect_uri', 'create_time', 'owner', 'mask', 'scopes', 'premises',
            'test_redirect_uri')

    def d_user(self, user):
        dict_ = self.d()
        dict_.update(dict(premises=self.check_premise(user)))
        return dict_

    def d_base(self):
        return self.dictor('app_name', 'app_id', 'logo', 'app_desc', 'user_num', 'create_time')

    @Excp.pack
    def modify_logo(self, logo):
        """修改应用logo"""
        self.validator(locals())
        from Base.qn import qn_public_manager
        if self.logo:
            qn_public_manager.delete_res(self.logo)
        self.logo = logo
        self.save()

    def belong(self, o_user):
        return self.owner == o_user

    def authentication(self, app_secret):
        return self.secret == app_secret

    def check_premise(self, user):
        premises = []
        for premise in self.premises.all():
            checker = Premise.get_checker(premise.name)
            if checker and callable(checker):
                error = Excp(checker(user)).error
            else:
                error = PremiseCheckerError.CHECKER_NOT_FOUND()
            p_dict = premise.d()
            p_dict['check'] = dict(
                identifier=ErrorJar.get_i(error),
                msg=error.get_msg(),
            )
            premises.append(p_dict)
        return premises


class UserApp(models.Model):
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
        max_length=16,
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
        max_length=20,
    )
    frequent_score = models.FloatField(
        verbose_name='频繁访问分数，按分值排序为常用应用',
        default=0,
    )
    last_score_changed_time = models.CharField(
        default=None,
        verbose_name='上一次分数变化的时间',
        max_length=20,
    )
    mark = models.PositiveSmallIntegerField(
        verbose_name='此用户的打分，0表示没打分',
        default=0,
    )

    def _readable_rebind(self):
        return float(self.last_auth_code_time) < self.app.field_change_time

    def d(self):
        return self.dictor('bind', 'mark', 'rebind', 'user_app_id')

    @classmethod
    @Excp.pack
    def get_by_user_app(cls, o_user, o_app):
        try:
            return cls.objects.get(user=o_user, app=o_app)
        except Exception:
            return AppError.USER_APP_NOT_FOUND

    @classmethod
    @Excp.pack
    def get_by_id(cls, user_app_id, check_bind=False):
        try:
            user_app = cls.objects.get(user_app_id=user_app_id)
        except Exception:
            return AppError.USER_APP_NOT_FOUND
        if check_bind and not user_app.bind:
            return AppError.APP_UNBINDED
        return user_app

    @classmethod
    def get_unique_id(cls):
        while True:
            user_app_id = get_random_string(length=8)
            try:
                cls.get_by_id(user_app_id)
            except Excp as ret:
                if ret.eis(AppError.USER_APP_NOT_FOUND):
                    return user_app_id

    @classmethod
    @Excp.pack
    def do_bind(cls, user, app):
        premise_list = app.check_premise(user)
        for premise in premise_list:
            error = getattr(PremiseCheckerError, premise['check']['identifier'], None)
            if error.eid != BaseError.OK.eid:
                return error

        crt_timestamp = datetime.datetime.now().timestamp()

        try:
            user_app = cls.get_by_user_app(user, app)
            user_app.bind = True
            user_app.last_auth_code_time = crt_timestamp
            user_app.frequent_score += 1
            user_app.last_score_changed_time = crt_timestamp
            user_app.save()
        except Excp as ret:
            if ret.eis(AppError.USER_APP_NOT_FOUND):
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
                except Exception:
                    return AppError.BIND_USER_APP
            else:
                return ret
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
        except Excp:
            return False

    @classmethod
    @Excp.pack
    def refresh_frequent_score(cls):
        from Config.models import Config
        crt_date = datetime.datetime.now().date()
        crt_time = datetime.datetime.now().timestamp()
        last_date = Config.get_value_by_key(CI.LAST_RE_FREQ_SCORE_DATE)
        last_date = datetime.datetime.strptime(last_date, '%Y-%m-%d').date()

        if last_date >= crt_date:
            return AppError.SCORE_REFRESHED

        from OAuth.api_views import OAUTH_TOKEN_EXPIRE_TIME

        Config.update_value(CI.LAST_RE_FREQ_SCORE_DATE, crt_date.strftime('%Y-%m-%d'))
        for user_app in cls.objects.all():
            if crt_time - float(
                    user_app.last_auth_code_time) > OAUTH_TOKEN_EXPIRE_TIME + 24 * 60 * 60:
                if crt_time - float(user_app.last_score_changed_time) > OAUTH_TOKEN_EXPIRE_TIME:
                    user_app.frequent_score /= 2
                    user_app.last_score_changed_time = crt_time
                    user_app.save()

    @Excp.pack
    def do_mark(self, mark):
        if mark < 1 or mark > 5:
            return AppError.MARK
        original_mark = self.mark
        self.mark = mark
        self.save()

        mark_list = list(map(int, self.app.mark.split('-')))
        if 5 >= original_mark > 0:
            mark_list[original_mark - 1] -= 1
        mark_list[mark - 1] += 1
        self.app.mark = '-'.join(map(str, mark_list))
        self.app.save()


class AppP:
    name, info, desc, redirect_uri, test_redirect_uri, secret = App.P(
        'name', 'info', 'desc', 'redirect_uri', 'test_redirect_uri', 'secret')
    scopes = P('scopes', '应用权限列表').process(Scope.list_to_scope_list)
    premises = P('premises', '应用要求列表').process(Premise.list_to_premise_list)

    app = P('app_id', '应用ID', 'app').process(App.get_by_id)
    user_app = P('user_app_id', '用户绑定应用ID', 'user_app').process(UserApp.get_by_id)
