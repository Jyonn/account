""" Adel Liu 180111

用户类
"""
import re

from django.db import models
from django.utils.crypto import get_random_string

from Base.common import deprint
from Base.decorator import field_validator
from Base.error import Error
from Base.response import Ret


class User(models.Model):
    """
    用户类
    根超级用户id=1
    """
    ROOT_ID = 1
    L = {
        'username': 32,
        'password': 32,
        'salt': 10,
        'nickname': 10,
        'avatar': 1024,
        'phone': 20,
    }
    email = models.EmailField(
        null=True,
        blank=True,
        default=None,
        verbose_name='暂时不用'
    )
    phone = models.CharField(
        default=None,
        unique=True,
        max_length=L['phone'],
    )
    username = models.CharField(
        max_length=L['username'],
        unique=True,
    )
    password = models.CharField(
        max_length=L['password'],
    )
    salt = models.CharField(
        max_length=L['salt'],
        default=None,
    )
    pwd_change_time = models.FloatField(
        null=True,
        blank=True,
        default=0,
    )
    avatar = models.CharField(
        default=None,
        null=True,
        blank=True,
        max_length=L['avatar'],
    )
    nickname = models.CharField(
        max_length=L['nickname'],
        default=None,
    )
    FIELD_LIST = ['email', 'username', 'password', 'avatar', 'nickname', 'phone']

    @staticmethod
    def _valid_username(username):
        """验证用户名合法"""
        valid_chars = '^[A-Za-z0-9_]{3,32}$'
        if re.match(valid_chars, username) is None:
            return Ret(Error.INVALID_USERNAME)
        return Ret()

    @staticmethod
    def _valid_password(password):
        """验证密码合法"""
        valid_chars = '^[A-Za-z0-9!@#$%^&*()_+-=,.?;:]{6,16}$'
        if re.match(valid_chars, password) is None:
            return Ret(Error.INVALID_PASSWORD)
        return Ret()

    @classmethod
    def _validate(cls, dict_):
        """验证传入参数是否合法"""
        return field_validator(dict_, cls)

    @staticmethod
    def hash_password(raw_password, salt=None):
        if not salt:
            salt = get_random_string(length=6)
        hash_password = User._hash(raw_password+salt)
        return salt, hash_password

    @classmethod
    def create(cls, username, password):
        """ 创建用户

        :param username: 用户名
        :param password: 密码
        :return: Ret对象，错误返回错误代码，成功返回用户对象
        """
        ret = cls._validate(locals())
        if ret.error is not Error.OK:
            return ret

        salt, hashed_password = User.hash_password(password)
        ret = User.get_user_by_username(username)
        if ret.error is Error.OK:
            return Ret(Error.USERNAME_EXIST)
        try:
            o_user = cls(
                username=username,
                password=hashed_password,
                salt=salt,
                email=None,
                avatar=None,
                nickname='',
            )
            o_user.save()
        except ValueError as err:
            deprint(str(err))
            return Ret(Error.ERROR_CREATE_USER)
        return Ret(o_user)

    def change_password(self, password, old_password):
        """修改密码"""
        ret = self._validate(locals())
        if ret.error is not Error.OK:
            return ret
        if self.password != User._hash(old_password):
            return Ret(Error.ERROR_PASSWORD)
        self.salt, self.password = User.hash_password(password)
        import datetime
        self.pwd_change_time = datetime.datetime.now().timestamp()
        self.save()
        return Ret()

    @staticmethod
    def _hash(s):
        from Base.common import md5
        return md5(s)

    @staticmethod
    def get_user_by_username(username):
        """根据用户名获取用户对象"""
        try:
            o_user = User.objects.get(username=username)
        except User.DoesNotExist as err:
            deprint(str(err))
            return Ret(Error.NOT_FOUND_USER)
        return Ret(o_user)

    @staticmethod
    def get_user_by_id(user_id):
        """根据用户ID获取用户对象"""
        try:
            o_user = User.objects.get(pk=user_id)
        except User.DoesNotExist as err:
            deprint(str(err))
            return Ret(Error.NOT_FOUND_USER)
        return Ret(o_user)

    def to_dict(self):
        """把用户对象转换为字典"""
        return dict(
            user_id=self.pk,
            username=self.username,
            avatar=self.get_avatar_url(),
            nickname=self.nickname,
        )

    def to_base_dict(self):
        """基本字典信息"""
        return dict(
            nickname=self.username[:-3]+'***',
            avatar=self.get_avatar_url(),
        )

    @staticmethod
    def authenticate(username, password):
        """验证用户名和密码是否匹配"""
        ret = User._validate(locals())
        if ret.error is not Error.OK:
            return ret
        try:
            o_user = User.objects.get(username=username)
        except User.DoesNotExist as err:
            deprint(str(err))
            return Ret(Error.NOT_FOUND_USER)
        salt, hashed_password = User.hash_password(password, o_user.salt)
        if hashed_password == o_user.password:
            return Ret(o_user)
        return Ret(Error.ERROR_PASSWORD)

    def get_avatar_url(self, small=True):
        """获取用户头像地址"""
        if self.avatar is None:
            return None
        from Base.qn import get_resource_url
        key = "%s-small" % self.avatar if small else self.avatar
        return get_resource_url(key)

    def modify_avatar(self, avatar):
        """修改用户头像"""
        ret = self._validate(locals())
        if ret.error is not Error.OK:
            return ret
        self.avatar = avatar
        self.save()
        return Ret()

    def modify_info(self, nickname):
        """修改用户信息"""
        if nickname is None:
            nickname = self.nickname
        ret = self._validate(locals())
        if ret.error is not Error.OK:
            return ret
        self.nickname = nickname
        self.save()
        return Ret()
