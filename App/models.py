import datetime

from django.db import models
from django.utils.crypto import get_random_string

from Base.common import deprint
from Base.validator import field_validator
from Base.error import Error
from Base.jtoken import jwt_e, JWType
from Base.response import Ret


class Premise(models.Model):
    """要求类，不满足要求无法进入应用"""
    L = {
        'name': 20,
        'desc': 20,
        'detail': 100,
    }
    name = models.CharField(
        verbose_name='要求英文简短名称',
        max_length=L['name'],
        unique=True,
    )
    desc = models.CharField(
        verbose_name='要求介绍',
        max_length=L['desc'],
    )
    detail = models.CharField(
        verbose_name='要求详细说明',
        max_length=L['detail'],
        default=None,
    )
    FIELD_LIST = ['name', 'desc', 'detail']

    class __PremiseNone:
        pass

    @classmethod
    def _validate(cls, d):
        return field_validator(d, cls)

    @classmethod
    def get_premise_by_id(cls, pid):
        try:
            o_premise = cls.objects.get(pk=pid)
        except cls.DoesNotExist as err:
            deprint('Premise-get_premise_by_id', str(err))
            return Ret(Error.NOT_FOUND_PREMISE)
        return Ret(o_premise)

    @classmethod
    def get_premise_by_name(cls, name, default=__PremiseNone()):
        try:
            o_premise = cls.objects.get(name=name)
        except Exception as err:
            deprint(str(err))
            if isinstance(default, cls.__PremiseNone):
                return Ret(Error.NOT_FOUND_PREMISE)
            else:
                return Ret(default)
        return Ret(o_premise)

    @classmethod
    def create(cls, name, desc, detail):
        ret = cls._validate(locals())
        if ret.error is not Error.OK:
            return ret

        try:
            o_premise = cls(
                name=name,
                desc=desc,
                detail=detail,
            )
            o_premise.save()
        except Exception as err:
            deprint('create-premise', str(err))
            return Ret(Error.ERROR_CREATE_PREMISE)
        return Ret(o_premise)

    def to_dict(self):
        return dict(
            name=self.name,
            desc=self.desc,
            detail=self.detail,
        )

    @classmethod
    def list_to_premise_list(cls, premises):
        premise_list = []
        if not isinstance(premises, list):
            return []
        for premise_name in premises:
            ret = cls.get_premise_by_name(premise_name)
            if ret.error is Error.OK:
                premise_list.append(ret.body)
        return premise_list

    @classmethod
    def get_premise_list(cls):
        premises = cls.objects.all()
        return [o_premise.to_dict() for o_premise in premises]


class Scope(models.Model):
    """权限类"""
    L = {
        'name': 20,
        'desc': 20,
        'detail': 100,
    }
    name = models.CharField(
        verbose_name='权限英文简短名称',
        max_length=L['name'],
        unique=True,
    )
    desc = models.CharField(
        verbose_name='权限介绍',
        max_length=L['desc'],
    )
    always = models.NullBooleanField(
        verbose_name="Null 可有可无 True 一直可选 False 一直不可选",
        default=None,
    )
    detail = models.CharField(
        verbose_name='权限详细说明',
        max_length=L['detail'],
        default=None,
    )
    FIELD_LIST = ['name', 'desc', 'detail']

    class __ScopeNone:
        pass

    @classmethod
    def _validate(cls, d):
        return field_validator(d, cls)

    @classmethod
    def get_scope_by_id(cls, sid):
        try:
            o_scope = cls.objects.get(pk=sid)
        except cls.DoesNotExist as err:
            deprint('Scope-get_scope_by_id', str(err))
            return Ret(Error.NOT_FOUND_SCOPE)
        return Ret(o_scope)

    @classmethod
    def get_scope_by_name(cls, name, default=__ScopeNone()):
        try:
            o_scope = cls.objects.get(name=name)
        except Exception as err:
            deprint(str(err))
            if isinstance(default, cls.__ScopeNone):
                return Ret(Error.NOT_FOUND_SCOPE)
            else:
                return Ret(default)
        return Ret(o_scope)

    @classmethod
    def create(cls, name, desc, detail):
        ret = cls._validate(locals())
        if ret.error is not Error.OK:
            return ret

        try:
            o_scope = cls(
                name=name,
                desc=desc,
                detail=detail,
                always=None,
            )
            o_scope.save()
        except Exception as err:
            deprint('create-scope', str(err))
            return Ret(Error.ERROR_CREATE_SCOPE)
        return Ret(o_scope)

    def to_dict(self):
        return dict(
            name=self.name,
            desc=self.desc,
            always=self.always,
            detail=self.detail,
        )

    @classmethod
    def list_to_scope_list(cls, scopes):
        scope_list = []
        if not isinstance(scopes, list):
            return []
        for scope_name in scopes:
            ret = cls.get_scope_by_name(scope_name)
            if ret.error is Error.OK and ret.body.always != False:  # 直接忽略false
                scope_list.append(ret.body)

        # 仍然存在always是True的但没有被添加的情况 于是double_check
        return cls.double_check(scope_list)

    @classmethod
    def get_scope_list(cls):
        scopes = cls.objects.all()
        return [o_scope.to_dict() for o_scope in scopes]

    @classmethod
    def double_check(cls, scope_list):
        total_scope_list = cls.objects.all()
        final_list = []
        for o_scope in total_scope_list:
            if o_scope.always:
                final_list.append(o_scope)
        for o_scope in scope_list:
            if o_scope.always is None:  # false被忽略，true已经添加
                final_list.append(o_scope)
        return final_list


class App(models.Model):
    L = {
        'name': 32,
        'id': 32,
        'secret': 32,
        'redirect_uri': 512,
        'desc': 32,
        'logo': 1024,
    }
    MIN_L = {
        'name': 2,
    }

    R_USER = 'user'
    R_OWNER = 'owner'
    R_LIST = [R_USER, R_OWNER]

    name = models.CharField(
        verbose_name='应用名称',
        max_length=L['name'],
        unique=True,
    )
    id = models.CharField(
        verbose_name='应用唯一ID',
        max_length=L['id'],
        primary_key=True,
    )
    secret = models.CharField(
        verbose_name='应用密钥',
        max_length=L['secret'],
    )
    redirect_uri = models.URLField(
        verbose_name='应用跳转URI',
        max_length=L['redirect_uri'],
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
        max_length=L['desc'],
        default=None,
    )
    logo = models.CharField(
        default=None,
        null=True,
        blank=True,
        max_length=L['logo'],
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

    FIELD_LIST = ['name', 'id', 'secret', 'redirect_uri', 'scopes', 'premises',
                  'desc', 'logo', 'mark', 'info']

    @classmethod
    def _validate(cls, d):
        return field_validator(d, cls)

    @classmethod
    def get_app_by_name(cls, name):
        try:
            o_app = cls.objects.get(name=name)
        except cls.DoesNotExist as err:
            deprint('App-get_app_by_name', str(err))
            return Ret(Error.NOT_FOUND_APP)
        return Ret(o_app)

    @classmethod
    def get_app_by_id(cls, app_id):
        try:
            o_app = cls.objects.get(pk=app_id)
        except cls.DoesNotExist as err:
            deprint('App-get_app_by_id', str(err))
            return Ret(Error.NOT_FOUND_APP)
        return Ret(o_app)

    @classmethod
    def get_unique_app_id(cls):
        while True:
            app_id = get_random_string(length=cls.L['id'])
            ret = cls.get_app_by_id(app_id)
            if ret.error == Error.NOT_FOUND_APP:
                return app_id
            deprint('generate app_id: %s, conflict.' % app_id)

    @classmethod
    def get_apps_by_owner(cls, owner):
        return cls.objects.filter(owner=owner)

    @classmethod
    def create(cls, name, desc, redirect_uri, scopes, premises, owner):
        ret = cls._validate(locals())
        if ret.error is not Error.OK:
            return ret

        ret = cls.get_app_by_name(name)
        if ret.error is Error.OK:
            return Ret(Error.EXIST_APP_NAME)

        try:
            o_app = cls(
                name=name,
                desc=desc,
                id=cls.get_unique_app_id(),
                secret=get_random_string(length=cls.L['secret']),
                redirect_uri=redirect_uri,
                owner=owner,
                field_change_time=datetime.datetime.now().timestamp(),
                info=None,
            )
            o_app.save()
            o_app.scopes.add(*scopes)
            o_app.premises.add(*premises)
            o_app.save()
        except Exception as err:
            deprint('App-create', str(err))
            return Ret(Error.ERROR_CREATE_APP, append_msg=str(err))
        return Ret(o_app)

    def modify(self, name, desc, info, redirect_uri, scopes, premises):
        """修改应用信息"""
        ret = self._validate(locals())
        if ret.error is not Error.OK:
            return ret
        self.name = name
        self.desc = desc
        self.info = info
        self.redirect_uri = redirect_uri
        self.scopes.remove()
        self.scopes.add(*scopes)
        self.premises.remove()
        self.premises.add(*premises)
        self.field_change_time = datetime.datetime.now().timestamp()
        try:
            self.save()
        except Exception as err:
            deprint(str(err))
            return Ret(Error.ERROR_MODIFY_APP, append_msg=str(err))
        return Ret()

    def to_dict(self, base=False):
        if base:
            return dict(
                app_name=self.name,
                app_id=self.id,
                logo=self.get_logo_url(),
                app_desc=self.desc,
                user_num=self.user_num,
            )
        scopes = self.scopes.all()
        scope_list = [o_scope.to_dict() for o_scope in scopes]
        premises = self.premises.all()
        premise_list = [o_premise.to_dict() for o_premise in premises]

        return dict(
            user_num=self.user_num,
            app_name=self.name,
            app_id=self.id,
            app_info=self.info,
            scopes=scope_list,
            premises=premise_list,
            redirect_uri=self.redirect_uri,
            logo=self.get_logo_url(),
            app_desc=self.desc,
            owner=self.owner.to_dict(base=True),
            mark=list(map(int, self.mark.split('-'))),
        )

    def get_logo_url(self, small=True):
        """获取应用logo地址"""
        if self.logo is None:
            return None
        from Base.qn import QN_PUBLIC_MANAGER
        key = "%s-small" % self.logo if small else self.logo
        return QN_PUBLIC_MANAGER.get_resource_url(key)

    def modify_logo(self, logo):
        """修改应用logo"""
        ret = self._validate(locals())
        if ret.error is not Error.OK:
            return ret
        from Base.qn import QN_PUBLIC_MANAGER
        if self.logo:
            ret = QN_PUBLIC_MANAGER.delete_res(self.logo)
            if ret.error is not Error.OK:
                return ret
        self.logo = logo
        self.save()
        return Ret()

    def belong(self, o_user):
        return self.owner == o_user

    def authentication(self, app_secret):
        return self.secret == app_secret


class UserApp(models.Model):
    """用户应用类"""
    L = {
        'user_app_id': 16,
        'auth_code': 32,
        'last_auth_code_time': 20,
        'last_score_changed_time': 20,
    }

    user = models.ForeignKey(
        'User.User',
        on_delete=models.CASCADE,
    )
    app = models.ForeignKey(
        'App.App',
        on_delete=models.CASCADE,
    )
    user_app_id = models.CharField(
        max_length=L['user_app_id'],
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
        max_length=L['last_auth_code_time'],
    )
    frequent_score = models.FloatField(
        verbose_name='频繁访问分数，按分值排序为常用应用',
        default=0,
    )
    last_score_changed_time = models.CharField(
        default=None,
        verbose_name='上一次分数变化的时间',
        max_length=L['last_score_changed_time'],
    )
    mark = models.PositiveSmallIntegerField(
        verbose_name='此用户的打分，0表示没打分',
        default=0,
    )

    def to_dict(self):
        return dict(
            bind=self.bind,
            mark=self.mark,
            rebind=float(self.last_auth_code_time) < self.app.field_change_time,
        )

    @classmethod
    def get_user_app_list_by_o_user(cls, o_user, frequent, count):
        app_list = cls.objects.filter(user=o_user, bind=True)
        if frequent:
            if count < 0:
                count = 3
            app_list = app_list.order_by('-frequent_score')[:count]
        return app_list

    @classmethod
    def get_user_app_by_o_user_o_app(cls, o_user, o_app):
        try:
            o_user_app = cls.objects.get(user=o_user, app=o_app)
        except cls.DoesNotExist as err:
            deprint('UserApp-get_user_app_by_o_user_o_app', str(err))
            return Ret(Error.NOT_FOUND_USER_APP)
        return Ret(o_user_app)

    @classmethod
    def get_user_app_by_user_app_id(cls, user_app_id, check_bind=False):
        try:
            o_user_app = cls.objects.get(user_app_id=user_app_id)
        except cls.DoesNotExist as err:
            deprint('UserApp-get_user_app_by_user_app_id')
            return Ret(Error.NOT_FOUND_USER_APP)
        if check_bind and not o_user_app.bind:
            return Ret(Error.APP_UNBINDED)
        return Ret(o_user_app)

    @classmethod
    def get_unique_user_app_id(cls):
        while True:
            user_app_id = get_random_string(length=cls.L['user_app_id'])
            ret = cls.get_user_app_by_user_app_id(user_app_id)
            if ret.error == Error.NOT_FOUND_USER_APP:
                return user_app_id
            deprint('generate user_app_id: %s, conflict.' % user_app_id)

    @classmethod
    def do_bind(cls, o_user, o_app):
        crt_timestamp = datetime.datetime.now().timestamp()

        ret = cls.get_user_app_by_o_user_o_app(o_user, o_app)
        if ret.error is Error.OK:
            o_user_app = ret.body
            if not isinstance(o_user_app, cls):
                return Ret(Error.STRANGE)
            o_user_app.bind = True
            o_user_app.last_auth_code_time = crt_timestamp
            o_user_app.frequent_score += 1
            o_user_app.last_score_changed_time = crt_timestamp
            o_user_app.save()
        else:
            try:
                o_user_app = cls(
                    user=o_user,
                    app=o_app,
                    user_app_id=cls.get_unique_user_app_id(),
                    bind=True,
                    last_auth_code_time=crt_timestamp,
                    frequent_score=1,
                    last_score_changed_time=crt_timestamp,
                )
                o_user_app.save()
                o_user_app.app.user_num += 1
                o_user_app.app.save()
            except Exception as err:
                deprint(str(err))
                return Ret(Error.ERROR_BIND_USER_APP)
        return jwt_e(dict(
            user_app_id=o_user_app.user_app_id,
            type=JWType.AUTH_CODE,
            ctime=crt_timestamp
        ), replace=False, expire_second=5 * 60)

    @classmethod
    def check_bind(cls, o_user, o_app):
        ret = cls.get_user_app_by_o_user_o_app(o_user, o_app)
        if ret.error is not Error.OK:
            return False
        o_user_app = ret.body
        if not isinstance(o_user_app, UserApp):
            deprint('UserApp-check_bind_strange')
            return False
        return o_user_app.bind

    @classmethod
    def refresh_frequent_score(cls):
        from Config.models import Config
        crt_date = datetime.datetime.now().date()
        crt_time = datetime.datetime.now().timestamp()
        last_date = Config.get_value_by_key('last-refresh-frequent-score-date').body
        last_date = datetime.datetime.strptime(last_date, '%Y-%m-%d').date()

        if last_date >= crt_date:
            return Ret(Error.SCORE_REFRESHED)

        from OAuth.api_views import OAUTH_TOKEN_EXPIRE_TIME

        Config.update_value('last-refresh-frequent-score-date', crt_date.strftime('%Y-%m-%d'))
        for o_user_app in cls.objects.all():
            if crt_time - float(o_user_app.last_auth_code_time) > OAUTH_TOKEN_EXPIRE_TIME + 24 * 60 * 60:
                if crt_time - float(o_user_app.last_score_changed_time) > OAUTH_TOKEN_EXPIRE_TIME:
                    o_user_app.frequent_score /= 2
                    o_user_app.last_score_changed_time = crt_time
                    o_user_app.save()

        return Ret()

    def do_mark(self, mark):
        if mark < 1 or mark > 5:
            return Ret(Error.ERROR_MARK)
        self.mark = mark
        self.save()

        mark_list = list(map(int, self.app.mark.split('-')))
        mark_list[mark - 1] += 1
        self.app.mark = '-'.join(map(str, mark_list))
        self.app.save()

        return Ret()

