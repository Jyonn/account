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
        'user_str_id': 32,
        'real_name': 32,
        'idcard': 18,
        'card_image_front': 1024,
        'card_image_back': 1024,
    }
    MIN_L = {
        'password': 6,
        'qitian': 4,
    }

    VERIFY_STATUS_UNVERIFIED = 0
    VERIFY_STATUS_UNDER_AUTO = 1
    VERIFY_STATUS_UNDER_MANUAL = 2
    VERIFY_STATUS_DONE = 3
    VERIFY_STATUS_TUPLE = (
        (VERIFY_STATUS_UNVERIFIED, '没有认证'),
        (VERIFY_STATUS_UNDER_AUTO, '自动认证阶段'),
        (VERIFY_STATUS_UNDER_MANUAL, '人工认证阶段'),
        (VERIFY_STATUS_DONE, '成功认证'),
    )

    VERIFY_CHINA = 0
    VERIFY_ABROAD = 1
    VERIFY_TUPLE = (
        (VERIFY_CHINA, '中国大陆身份证认证'),
        (VERIFY_ABROAD, '其他地区身份认证'),
    )

    user_str_id = models.CharField(
        verbose_name='唯一随机用户ID，弃用user_id',
        default=None,
        null=True,
        blank=True,
        max_length=L['user_str_id'],
        unique=True,
    )
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
    birthday = models.DateField(
        verbose_name='生日',
        default=None,
        null=True,
    )
    email = models.EmailField(
        verbose_name='邮箱',
        default=None,
        null=True,
    )

    verify_status = models.SmallIntegerField(
        verbose_name='是否通过实名认证',
        default=0,
        choices=VERIFY_STATUS_TUPLE,
    )
    real_verify_type = models.SmallIntegerField(
        verbose_name='实名认证类型',
        default=None,
        null=True,
    )
    real_name = models.CharField(
        verbose_name='真实姓名',
        default=None,
        max_length=L['real_name'],
        null=True,
    )
    male = models.NullBooleanField(
        verbose_name='是否为男性',
        default=None,
        null=True,
    )
    idcard = models.CharField(
        verbose_name='身份证号',
        default=None,
        max_length=L['idcard'],
        choices=VERIFY_TUPLE,
        null=True,
    )
    card_image_front = models.CharField(
        verbose_name='身份证正面照',
        max_length=L['card_image_front'],
        default=None,
        null=True,
    )
    card_image_back = models.CharField(
        verbose_name='身份证背面照',
        max_length=L['card_image_back'],
        default=None,
        null=True,
    )
    is_dev = models.BooleanField(
        verbose_name='是否开发者',
        default=False,
    )

    FIELD_LIST = [
        'qitian', 'password', 'avatar', 'nickname', 'phone',
        'description', 'birthday', 'email', 'is_dev']

    @classmethod
    def get_unique_user_str_id(cls):
        while True:
            user_str_id = get_random_string(length=cls.L['user_str_id'])
            ret = cls.get_user_by_str_id(user_str_id)
            if ret.error == Error.NOT_FOUND_USER:
                return user_str_id
            deprint('generate user_str_id: %s, conflict.' % user_str_id)

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

    @staticmethod
    def _valid_birthday(birthday):
        """验证生日是否合法"""
        import datetime
        if not isinstance(birthday, datetime.date):
            return Ret(Error.ERROR_DATE_FORMAT)
        if birthday > datetime.datetime.now().date():
            return Ret(Error.ERROR_BIRTHDAY_FORMAT)
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
                user_str_id=cls.get_unique_user_str_id(),
                birthday=None,
                verify_status=cls.VERIFY_STATUS_UNVERIFIED,
                is_dev=False,
            )
            o_user.save()
        except ValueError as err:
            deprint(str(err))
            return Ret(Error.ERROR_CREATE_USER)
        return Ret(o_user)

    def modify_password(self, password):
        ret = self._validate(locals())
        if ret.error is not Error.OK:
            return ret
        self.salt, self.password = User.hash_password(password)
        import datetime
        self.pwd_change_time = datetime.datetime.now().timestamp()
        self.save()
        return Ret()

    def change_password(self, password, old_password):
        """修改密码"""
        ret = self._validate(locals())
        if ret.error is not Error.OK:
            return ret
        if self.password != User._hash(old_password+self.salt):
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

    @classmethod
    def get_user_by_str_id(cls, user_str_id):
        try:
            o_user = cls.objects.get(user_str_id=user_str_id)
        except cls.DoesNotExist as err:
            deprint(str(err))
            return Ret(Error.NOT_FOUND_USER)
        return Ret(o_user)

    @classmethod
    def get_user_by_phone(cls, phone):
        """根据手机号获取用户对象"""
        try:
            o_user = cls.objects.get(phone=phone)
        except cls.DoesNotExist as err:
            deprint(str(err))
            return Ret(Error.NOT_FOUND_USER, append_msg='，手机号未注册')
        return Ret(o_user)

    @classmethod
    def get_user_by_qitian(cls, qitian_id):
        try:
            o_user = cls.objects.get(qitian=qitian_id)
        except cls.DoesNotExist as err:
            deprint(str(err))
            return Ret(Error.NOT_FOUND_USER, append_msg='，不存在的齐天号')
        return Ret(o_user)

    @classmethod
    def get_user_by_id(cls, user_id):
        """根据用户ID获取用户对象"""
        try:
            o_user = cls.objects.get(pk=user_id)
        except cls.DoesNotExist as err:
            deprint(str(err))
            return Ret(Error.NOT_FOUND_USER)
        return Ret(o_user)

    def allow_qitian_modify(self):
        return self.qitian_modify_time == 0

    def to_dict(self, oauth=False, base=False):
        """把用户对象转换为字典"""
        if oauth:
            return dict(
                avatar=self.get_avatar_url(),
                nickname=self.nickname,
                description=self.description,
            )
        elif base:
            return dict(
                user_str_id=self.user_str_id,
                avatar=self.get_avatar_url(),
                nickname=self.nickname,
                description=self.description,
            )
        else:
            return dict(
                birthday=self.birthday.strftime('%Y-%m-%d') if self.birthday else None,
                user_str_id=self.user_str_id,
                qitian=self.qitian,
                avatar=self.get_avatar_url(),
                nickname=self.nickname,
                description=self.description,
                allow_qitian_modify=int(self.allow_qitian_modify()),
                verify_status=self.verify_status,
                verify_type=self.real_verify_type,
                is_dev=self.is_dev,
            )

    @classmethod
    def authenticate(cls, qitian, phone, password):
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

    def get_card_urls(self):
        from Base.qn import QN_RES_MANAGER
        front_url = QN_RES_MANAGER.get_resource_url(self.card_image_front) \
            if self.card_image_front else None
        back_url = QN_RES_MANAGER.get_resource_url(self.card_image_back) \
            if self.card_image_back else None
        return dict(
            front=front_url,
            back=back_url,
        )

    def modify_avatar(self, avatar):
        """修改用户头像"""
        ret = self._validate(locals())
        if ret.error is not Error.OK:
            return ret

        if self.avatar:
            from Base.qn import QN_PUBLIC_MANAGER
            ret = QN_PUBLIC_MANAGER.delete_res(self.avatar)
            if ret.error is not Error.OK:
                return ret
        self.avatar = avatar
        self.save()
        return Ret()

    def upload_verify_front(self, card_image_front):
        ret = self._validate(locals())
        if ret.error is not Error.OK:
            return ret

        from Base.qn import QN_RES_MANAGER
        if self.card_image_front:
            ret = QN_RES_MANAGER.delete_res(self.card_image_front)
            if ret.error is not Error.OK:
                return ret

        self.card_image_front = card_image_front
        self.save()
        return Ret(QN_RES_MANAGER.get_resource_url(self.card_image_front + '-small'))

    def upload_verify_back(self, card_image_back):
        ret = self._validate(locals())
        if ret.error is not Error.OK:
            return ret

        from Base.qn import QN_RES_MANAGER
        if self.card_image_back:
            ret = QN_RES_MANAGER.delete_res(self.card_image_back)
            if ret.error is not Error.OK:
                return ret

        self.card_image_back = card_image_back
        self.save()
        return Ret(QN_RES_MANAGER.get_resource_url(self.card_image_back + '-small'))

    def modify_info(self, nickname, description, qitian, birthday):
        """修改用户信息"""
        if nickname is None:
            nickname = self.nickname
        if description is None:
            description = self.description
        if qitian is None:
            qitian = self.qitian
        if birthday is None or (self.verify_status and self.real_verify_type == User.VERIFY_CHINA):
            birthday = self.birthday
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
        self.birthday = birthday
        self.save()
        return Ret()

    def update_card_info(self, real_name, male, idcard, birthday):
        ret = self._validate(locals())
        if ret.error is not Error.OK:
            return ret

        self.real_name = real_name
        self.male = male
        self.idcard = idcard
        self.birthday = birthday
        try:
            self.save()
        except Exception as err:
            deprint(str(err))
            return Ret(Error.AUTO_VERIFY_FAILED)

        return Ret()

    def update_verify_status(self, status):
        self.verify_status = status
        self.save()

    def update_verify_type(self, verify_type):
        self.real_verify_type = verify_type
        self.save()

    def developer(self):
        self.is_dev = True
        self.save()
