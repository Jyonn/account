import datetime

from django.db import models
from django.utils.crypto import get_random_string

from Base.common import deprint
from Base.decorator import field_validator
from Base.error import Error
from Base.response import Ret


class Scope(models.Model):
    """权限类"""
    L = {
        'name': 10,
        'desc': 20,
    }
    name = models.CharField(
        verbose_name='权限英文简短名称',
        max_length=L['name'],
    )
    desc = models.CharField(
        verbose_name='权限介绍',
        max_length=L['desc']
    )
    FIELD_LIST = ['name', 'desc']

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
    def create(cls, name, desc):
        ret = cls._validate(locals())
        if ret.error is not Error.OK:
            return ret

        try:
            o_scope = cls(
                name=name,
                desc=desc,
            )
            o_scope.save()
        except Exception as err:
            deprint('create-scope', str(err))
            return Ret(Error.ERROR_CREATE_SCOPE)
        return Ret(o_scope)

    def to_dict(self):
        return dict(
            sid=self.pk,
            name=self.name,
            desc=self.desc,
        )

    @classmethod
    def list_to_scope_list(cls, scopes):
        scope_list = []
        if not isinstance(scopes, list):
            return []
        for i, sid in scopes:
            ret = cls.get_scope_by_id(sid)
            if ret.error is Error.OK:
                scope_list.append(ret.body)
        return scope_list


class App(models.Model):
    L = {
        'name': 32,
        'id': 32,
        'secret': 32,
        'redirect_uri': 512,
    }
    MIN_L = {
        'name': 2,
    }

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

    FIELD_LIST = ['name', 'id', 'secret', 'redirect_uri', 'scope']

    @classmethod
    def _validate(cls, d, allow_none=False):
        return field_validator(d, cls, allow_none=allow_none)

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
    def get_apps_by_owner(cls, owner):
        return cls.objects.filter(owner=owner)

    @classmethod
    def create(cls, name, redirect_uri, scopes, owner):
        ret = cls._validate(locals())
        if ret.error is not Error.OK:
            return ret

        ret = cls.get_app_by_name(name)
        if ret.error is Error.OK:
            return Ret(Error.EXIST_APP_NAME)

        id_ = get_random_string(length=cls.L['id'])
        secret = get_random_string(length=cls.L['secret'])

        try:
            o_app = cls(
                name=name,
                id=id_,
                secret=secret,
                redirect_uri=redirect_uri,
                owner=owner,
            )
            o_app.save()
            o_app.scopes.add(*scopes)
            o_app.save()
        except Exception as err:
            deprint('App-create', str(err))
            return Ret(Error.ERROR_CREATE_APP, append_msg=str(err))
        return Ret(o_app)

    def modify(self, name, redirect_uri, scopes):
        ret = self._validate(locals(), allow_none=True)
        if ret.error is not Error.OK:
            return ret
        if name:
            self.name = name
        if redirect_uri:
            self.redirect_uri = redirect_uri
        if scopes:
            self.scopes.remove()
            self.scopes.add(*scopes)
        self.field_change_time = datetime.datetime.now().timestamp()
        try:
            self.save()
        except Exception as err:
            deprint(str(err))
            return Ret(Error.ERROR_MODIFY_APP, append_msg=str(err))
        return Ret()

    def to_dict(self):
        scopes = self.scopes.all()
        scope_list = [o_scope.to_dict() for o_scope in scopes]
        return dict(
            app_name=self.name,
            app_id=self.id,
            app_secret=self.secret,
            scopes=scope_list,
            redirect_uri=self.redirect_uri,
        )


class UserApp(models.Model):
    """用户应用类"""
    L = {
        'user_app_id': 8,
        'auth_code': 32,
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
    )
    bind = models.BooleanField(
        default=False,
        verbose_name='用户是否绑定应用',
    )

    last_auth_code_time = models.FloatField(
        default=0,
        verbose_name='上一次申请auth_code的时间，防止被多次使用',
    )
