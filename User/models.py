""" Adel Liu 180111

用户类
"""
import datetime
import re

from SmartDjango import models, Excp, E, P
from django.utils.crypto import get_random_string

from Base.idcard import IDCardError


@E.register
class UserError:
    CREATE_USER = E("存储用户错误")
    PASSWORD = E("密码错误")
    USER_NOT_FOUND = E("不存在的用户")
    INVALID_QITIAN = E("齐天号只能包含字母数字以及下划线")
    INVALID_PASSWORD = E("密码存在特殊字符")
    INVALID_USERNAME_FIRST = E("用户名首字符只能是字母")
    INVALID_USERNAME = E("用户名只能包含字母数字和下划线")
    ERROR_DATE_FORMAT = E("日期格式错误")
    BIRTHDAY_FORMAT = E("错误的生日时间")
    PHONE_EXIST = E("手机号已注册")
    QITIAN_EXIST = E("已存在此齐天号")


class User(models.Model):
    """
    用户类
    根超级用户id=1
    """
    ROOT_ID = 1

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
        verbose_name='唯一随机用户ID',
        default=None,
        null=True,
        blank=True,
        max_length=32,
        unique=True,
    )
    qitian = models.CharField(
        default=None,
        unique=True,
        max_length=20,
        min_length=4,
    )
    phone = models.CharField(
        default=None,
        unique=True,
        max_length=20,
    )
    password = models.CharField(
        max_length=32,
        min_length=6,
    )
    salt = models.CharField(
        max_length=10,
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
        max_length=1024,
    )
    nickname = models.CharField(
        max_length=10,
        default=None,
    )
    description = models.CharField(
        max_length=20,
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
        max_length=32,
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
        max_length=18,
        choices=VERIFY_TUPLE,
        null=True,
    )
    card_image_front = models.CharField(
        verbose_name='身份证正面照',
        max_length=1024,
        default=None,
        null=True,
    )
    card_image_back = models.CharField(
        verbose_name='身份证背面照',
        max_length=1024,
        default=None,
        null=True,
    )
    is_dev = models.BooleanField(
        verbose_name='是否开发者',
        default=False,
    )

    @classmethod
    @Excp.pack
    def get_unique_id(cls):
        while True:
            user_str_id = get_random_string(length=6)
            try:
                cls.get_by_str_id(user_str_id)
            except Excp as ret:
                if ret.eis(UserError.USER_NOT_FOUND):
                    return user_str_id

    @classmethod
    @Excp.pack
    def get_unique_qitian(cls):
        while True:
            qitian_id = get_random_string(length=8)
            try:
                cls.get_by_qitian(qitian_id)
            except Excp as ret:
                if ret.eis(UserError.USER_NOT_FOUND):
                    return qitian_id

    @staticmethod
    @Excp.pack
    def _valid_qitian(qitian):
        """验证齐天号合法"""
        valid_chars = '^[A-Za-z0-9_]{4,20}$'
        if re.match(valid_chars, qitian) is None:
            return UserError.INVALID_QITIAN

    @staticmethod
    @Excp.pack
    def _valid_password(password):
        """验证密码合法"""
        valid_chars = '^[A-Za-z0-9!@#$%^&*()_+-=,.?;:]{6,16}$'
        if re.match(valid_chars, password) is None:
            return UserError.INVALID_PASSWORD

    @staticmethod
    @Excp.pack
    def _valid_birthday(birthday):
        """验证生日是否合法"""
        import datetime
        if birthday > datetime.datetime.now().date():
            return UserError.BIRTHDAY_FORMAT

    @staticmethod
    def hash_password(raw_password, salt=None):
        if not salt:
            salt = get_random_string(length=6)
        hash_password = User._hash(raw_password+salt)
        return salt, hash_password

    @classmethod
    @Excp.pack
    def create(cls, phone, password):
        salt, hashed_password = User.hash_password(password)
        try:
            User.get_by_phone(phone)
            return UserError.PHONE_EXIST
        except Excp:
            try:
                user = cls(
                    qitian=cls.get_unique_qitian(),
                    phone=phone,
                    password=hashed_password,
                    salt=salt,
                    avatar=None,
                    nickname='',
                    description=None,
                    qitian_modify_time=0,
                    user_str_id=cls.get_unique_id(),
                    birthday=None,
                    verify_status=cls.VERIFY_STATUS_UNVERIFIED,
                    is_dev=False,
                )
                user.save()
            except Exception:
                return UserError.CREATE_USER
        return user

    @Excp.pack
    def modify_password(self, password):
        self.salt, self.password = User.hash_password(password)
        import datetime
        self.pwd_change_time = datetime.datetime.now().timestamp()
        self.save()

    @Excp.pack
    def change_password(self, password, old_password):
        """修改密码"""
        if self.password != User._hash(old_password+self.salt):
            return UserError.PASSWORD
        self.salt, self.password = User.hash_password(password)
        import datetime
        self.pwd_change_time = datetime.datetime.now().timestamp()
        self.save()

    @staticmethod
    def _hash(s):
        from Base.common import md5
        return md5(s)

    @classmethod
    @Excp.pack
    def get_by_str_id(cls, user_str_id):
        try:
            return cls.objects.get(user_str_id=user_str_id)
        except cls.DoesNotExist:
            return UserError.USER_NOT_FOUND

    @classmethod
    @Excp.pack
    def get_by_phone(cls, phone):
        """根据手机号获取用户对象"""
        try:
            return cls.objects.get(phone=phone)
        except cls.DoesNotExist:
            return UserError.USER_NOT_FOUND('手机号未注册')

    @classmethod
    @Excp.pack
    def get_by_qitian(cls, qitian_id):
        try:
            return cls.objects.get(qitian=qitian_id)
        except cls.DoesNotExist:
            return UserError.USER_NOT_FOUND('不存在的齐天号')

    @classmethod
    def get_by_id(cls, user_id):
        """根据用户ID获取用户对象"""
        try:
            return cls.objects.get(pk=user_id)
        except cls.DoesNotExist:
            return UserError.USER_NOT_FOUND

    def allow_qitian_modify(self):
        return self.qitian_modify_time == 0

    def _readable_avatar(self):
        return self.get_avatar_url()

    def _readable_birthday(self):
        return self.birthday.strftime('%Y-%m-%d') if self.birthday else None

    def _readable_allow_qitian_modify(self):
        return int(self.allow_qitian_modify())

    def d_oauth(self):
        return self.dictor('avatar', 'nickname', 'description')

    def d_base(self):
        return self.dictor('user_str_id', 'avatar', 'nickname', 'description')

    def d(self):
        return self.dictor('birthday', 'user_str_id', 'qitian', 'avatar', 'nickname',
                           'description', 'allow_qitian_modify', 'verify_status',
                           'verify_type', 'is_dev')

    @classmethod
    @Excp.pack
    def authenticate(cls, qitian, phone, password):
        """验证手机号和密码是否匹配"""
        if qitian:
            user = cls.get_by_qitian(qitian)
        else:
            user = cls.get_by_phone(phone)

        salt, hashed_password = User.hash_password(password, user.salt)
        if hashed_password == user.password:
            return user
        return UserError.PASSWORD

    def get_avatar_url(self, small=True):
        """获取用户头像地址"""
        if self.avatar is None:
            return None
        from Base.qn import qn_public_manager
        key = "%s-small" % self.avatar if small else self.avatar
        return qn_public_manager.get_resource_url(key)

    def get_card_urls(self):
        from Base.qn import qn_res_manager
        front_url = qn_res_manager.get_resource_url(self.card_image_front) \
            if self.card_image_front else None
        back_url = qn_res_manager.get_resource_url(self.card_image_back) \
            if self.card_image_back else None
        return dict(
            front=front_url,
            back=back_url,
        )

    @Excp.pack
    def modify_avatar(self, avatar):
        """修改用户头像"""
        if self.avatar:
            from Base.qn import qn_public_manager
            qn_public_manager.delete_res(self.avatar)
        self.avatar = avatar
        self.save()

    @Excp.pack
    def upload_verify_front(self, card_image_front):
        from Base.qn import qn_res_manager
        if self.card_image_front:
            qn_res_manager.delete_res(self.card_image_front)

        self.card_image_front = card_image_front
        self.save()
        qn_res_manager.get_resource_url(self.card_image_front + '-small')

    @Excp.pack
    def upload_verify_back(self, card_image_back):
        from Base.qn import qn_res_manager
        if self.card_image_back:
            qn_res_manager.delete_res(self.card_image_back)

        self.card_image_back = card_image_back
        self.save()
        qn_res_manager.get_resource_url(self.card_image_back + '-small')

    @Excp.pack
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

        if self.allow_qitian_modify():
            if self.qitian != qitian:
                try:
                    self.get_by_qitian(qitian)
                except Excp as ret:
                    if ret.eis(UserError.USER_NOT_FOUND):
                        self.qitian = qitian
                        self.qitian_modify_time += 1
                    else:
                        return UserError.QITIAN_EXIST
        self.nickname = nickname
        self.description = description
        self.birthday = birthday
        self.save()

    @Excp.pack
    def update_card_info(self, real_name, male, idcard, birthday):
        self.validator(locals())
        self.real_name = real_name
        self.male = male
        self.idcard = idcard
        self.birthday = birthday
        try:
            self.save()
        except Exception:
            return IDCardError.AUTO_VERIFY_FAILED

    def update_verify_status(self, status):
        self.verify_status = status
        self.save()

    def update_verify_type(self, verify_type):
        self.real_verify_type = verify_type
        self.save()

    def developer(self):
        self.is_dev = True
        self.save()


class UserP:
    birthday, password, nickname, description, qitian, idcard, male, real_name = User.P(
        'birthday', 'password', 'nickname', 'description', 'qitian', 'idcard', 'male',
        'real_name')

    user = P('user_id', '用户唯一ID', 'user').process(User.get_by_str_id)
    back = P('back', '侧别').process(int)

    birthday.process(lambda s: datetime.datetime.strptime(s, '%Y-%m-%d').date(), begin=True)
