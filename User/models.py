""" Adel Liu 180111

用户类
"""
import re

from django.db import models
from django.utils.crypto import get_random_string

from Base.common import deprint
from Base.validator import field_validator
from Base.error import Error
from Base.response import Ret


class User(models.Model):
    """
    用户类
    根超级用户id=1
    """
    ROOT_ID = 1
    L = {
        'password': 32,
        'salt': 10,
        'nickname': 10,
        'avatar': 1024,
        'phone': 20,
        'qitian': 20,
        'description': 20,
    }
    MIN_L = {
        'password': 6,
        'qitian': 4,
    }
    qitian = models.CharField(
        default=None,
        unique=True,
        max_length=L['qitian'],
    )
    phone = models.CharField(
        default=None,
        unique=True,
        max_length=L['phone'],
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
    description = models.CharField(
        max_length=L['description'],
        default=None,
        blank=True,
        null=True,
    )
    qitian_modify_time = models.IntegerField(
        verbose_name='齐天号被修改的次数',
        help_text='一般只能修改一次',
        default=0,
    )
    FIELD_LIST = ['qitian', 'password', 'avatar', 'nickname', 'phone', 'description']

    @classmethod
    def get_unique_qitian_id(cls):
        while True:
            qitian_id = get_random_string(length=8)
            ret = cls.get_user_by_qitian(qitian_id)
            if ret.error == Error.NOT_FOUND_USER:
                return qitian_id
            deprint('generate res_str_id: %s, conflict.' % qitian_id)

    @staticmethod
    def _valid_qitian(qitian):
        """验证齐天号合法"""
        valid_chars = '^[A-Za-z0-9_]{4,20}$'
        if re.match(valid_chars, qitian) is None:
            return Ret(Error.INVALID_QITIAN)
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
    def create(cls, phone, password):
        """ 创建用户

        :param phone: 手机号
        :param password: 密码
        :return: Ret对象，错误返回错误代码，成功返回用户对象
        """
        ret = cls._validate(locals())
        if ret.error is not Error.OK:
            return ret

        salt, hashed_password = User.hash_password(password)
        ret = User.get_user_by_phone(phone)
        if ret.error is Error.OK:
            return Ret(Error.PHONE_EXIST)
        try:
            o_user = cls(
                qitian=cls.get_unique_qitian_id(),
                phone=phone,
                password=hashed_password,
                salt=salt,
                avatar=None,
                nickname='',
                description=None,
                qitian_modify_time=0,
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
    def get_user_by_phone(phone):
        """根据用户名获取用户对象"""
        try:
            o_user = User.objects.get(phone=phone)
        except User.DoesNotExist as err:
            deprint(str(err))
            return Ret(Error.NOT_FOUND_USER)
        return Ret(o_user)

    @staticmethod
    def get_user_by_qitian(qitian_id):
        try:
            o_user = User.objects.get(qitian=qitian_id)
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

    def allow_qitian_modify(self):
        return self.qitian_modify_time == 0

    def to_dict(self, oauth=False):
        """把用户对象转换为字典"""
        if oauth:
            return dict(
                avatar=self.get_avatar_url(),
                nickname=self.nickname,
                description=self.description,
            )
        else:
            return dict(
                user_id=self.pk,
                qitian=self.qitian,
                avatar=self.get_avatar_url(),
                nickname=self.nickname,
                description=self.description,
                allow_qitian_modify=int(self.allow_qitian_modify()),
                bind_phone=int(self.phone is not None),
            )

    @classmethod
    def authenticate(cls, qitian, phone, password):
        print(qitian, phone, password)
        """验证手机号和密码是否匹配"""
        if qitian:
            ret = cls.get_user_by_qitian(qitian)
        else:
            ret = cls.get_user_by_phone(phone)
        if ret.error is not Error.OK:
            return ret
        o_user = ret.body

        salt, hashed_password = User.hash_password(password, o_user.salt)
        if hashed_password == o_user.password:
            return Ret(o_user)
        return Ret(Error.ERROR_PASSWORD)

    def get_avatar_url(self, small=True):
        """获取用户头像地址"""
        if self.avatar is None:
            return None
        from Base.qn import QN_PUBLIC_MANAGER
        key = "%s-small" % self.avatar if small else self.avatar
        return QN_PUBLIC_MANAGER.get_resource_url(key)

    def modify_avatar(self, avatar):
        """修改用户头像"""
        ret = self._validate(locals())
        if ret.error is not Error.OK:
            return ret

        self.avatar = avatar
        self.save()
        return Ret()

    def modify_info(self, nickname, description, qitian):
        """修改用户信息"""
        if nickname is None:
            nickname = self.nickname
        if description is None:
            description = self.description
        if qitian is None:
            qitian = self.qitian
        ret = self._validate(locals())
        if ret.error is not Error.OK:
            return ret

        if self.allow_qitian_modify():
            if self.qitian != qitian:
                ret = self.get_user_by_qitian(qitian)
                if ret.error == Error.NOT_FOUND_USER:
                    self.qitian = qitian
                    self.qitian_modify_time += 1
                else:
                    return Ret(Error.QITIAN_EXIST)
        self.nickname = nickname
        self.description = description
        self.save()
        return Ret()
