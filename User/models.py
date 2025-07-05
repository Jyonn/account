from diq import Dictify
from django.db import models
from django.utils.crypto import get_random_string

from Base.idcard import IDCardErrors
from User.validators import UserErrors, UserValidator


class User(models.Model, Dictify):
    """
    用户类
    根超级用户id=1
    """

    vldt = UserValidator

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
        max_length=vldt.MAX_USER_STR_ID_LENGTH,
        unique=True,
    )

    qitian = models.CharField(
        default=None,
        unique=True,
        max_length=vldt.MAX_QITIAN_LENGTH,
        validators=[vldt.qitian]
    )

    phone = models.CharField(
        default=None,
        unique=True,
        max_length=vldt.MAX_PHONE_LENGTH,
    )

    password = models.CharField(
        max_length=vldt.MAX_PASSWORD_LENGTH,
        validators=[vldt.password]
    )

    salt = models.CharField(
        max_length=vldt.MAX_SALT_LENGTH,
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
        max_length=vldt.MAX_AVATAR_LENGTH,
    )

    nickname = models.CharField(
        max_length=vldt.MAX_NICKNAME_LENGTH,
        default=None,
    )

    description = models.CharField(
        max_length=vldt.MAX_DESCRIPTION_LENGTH,
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
        validators=[vldt.birthday]
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
        max_length=vldt.MAX_REAL_NAME_LENGTH,
        null=True,
    )

    male = models.BooleanField(
        verbose_name='是否为男性',
        default=None,
        null=True,
        blank=True,
    )

    idcard = models.CharField(
        verbose_name='身份证号',
        default=None,
        max_length=vldt.MAX_IDCARD_LENGTH,
        choices=VERIFY_TUPLE,
        null=True,
    )

    card_image_front = models.CharField(
        verbose_name='身份证正面照',
        max_length=vldt.MAX_CARD_IMAGE_FRONT_LENGTH,
        default=None,
        null=True,
    )

    card_image_back = models.CharField(
        verbose_name='身份证背面照',
        max_length=vldt.MAX_CARD_IMAGE_BACK_LENGTH,
        default=None,
        null=True,
    )

    is_dev = models.BooleanField(
        verbose_name='是否开发者',
        default=False,
    )

    @classmethod
    def get_unique_id(cls):
        while True:
            user_str_id = get_random_string(length=cls.vldt.DEFAULT_USER_STR_ID_LENGTH)
            try:
                cls.get_by_str_id(user_str_id)
            except UserErrors.USER_NOT_FOUND:
                return user_str_id

    @classmethod
    def get_unique_qitian(cls):
        while True:
            qitian_id = get_random_string(length=cls.vldt.DEFAULT_QITIAN_LENGTH)
            try:
                cls.get_by_qitian(qitian_id)
            except UserErrors.USER_NOT_FOUND:
                return qitian_id

    @classmethod
    def hash_password(cls, raw_password, salt=None):
        if not salt:
            salt = get_random_string(length=cls.vldt.DEFAULT_SALT_LENGTH)
        hash_password = User._hash(raw_password + salt)
        return salt, hash_password

    @classmethod
    def create(cls, phone, password):
        salt, hashed_password = cls.hash_password(password)

        User.exist_with_phone(phone)

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
        except Exception as err:
            raise UserErrors.CREATE_USER(details=err)
        return user

    def modify_password(self, password):
        self.salt, self.password = User.hash_password(password)
        import datetime
        self.pwd_change_time = datetime.datetime.now().timestamp()
        self.save()

    def change_password(self, password, old_password):
        """修改密码"""
        if self.password != User._hash(old_password + self.salt):
            raise UserErrors.PASSWORD
        self.salt, self.password = User.hash_password(password)
        import datetime
        self.pwd_change_time = datetime.datetime.now().timestamp()
        self.save()

    @staticmethod
    def _hash(s):
        from Base.common import md5
        return md5(s)

    @classmethod
    def get_by_str_id(cls, user_str_id):
        try:
            return cls.objects.get(user_str_id=user_str_id)
        except cls.DoesNotExist:
            raise UserErrors.USER_NOT_FOUND

    @classmethod
    def get_by_phone(cls, phone):
        """根据手机号获取用户对象"""
        try:
            return cls.objects.get(phone=phone)
        except cls.DoesNotExist:
            raise UserErrors.USER_NOT_FOUND('手机号未注册')

    @classmethod
    def exist_with_phone(cls, phone):
        try:
            cls.objects.get(phone=phone)
        except cls.DoesNotExist:
            return
        raise UserErrors.PHONE_EXIST

    @classmethod
    def get_by_qitian(cls, qitian_id):
        try:
            return cls.objects.get(qitian=qitian_id)
        except cls.DoesNotExist:
            raise UserErrors.USER_NOT_FOUND('不存在的齐天号')

    @classmethod
    def exist_with_qitian(cls, qitian_id):
        try:
            cls.objects.get(qitian=qitian_id)
        except cls.DoesNotExist:
            return
        raise UserErrors.QITIAN_EXIST

    @classmethod
    def get_by_id(cls, user_id):
        """根据用户ID获取用户对象"""
        try:
            return cls.objects.get(pk=user_id)
        except cls.DoesNotExist:
            raise UserErrors.USER_NOT_FOUND

    def allow_qitian_modify(self):
        return self.qitian_modify_time == 0

    def _dictify_avatar(self):
        return self.get_avatar_url()

    def _dictify_birthday(self):
        return self.birthday.strftime('%Y-%m-%d') if self.birthday else None

    def _dictify_allow_qitian_modify(self):
        return int(self.allow_qitian_modify())

    def d_oauth(self):
        return self.dictify('avatar', 'nickname', 'description')

    def d_base(self):
        return self.dictify('user_str_id', 'avatar', 'nickname', 'description')

    def d(self):
        return self.dictify('birthday', 'user_str_id', 'qitian', 'avatar', 'nickname',
                            'description', 'allow_qitian_modify', 'verify_status',
                            'verify_type', 'is_dev')

    @classmethod
    def authenticate(cls, qitian, phone, password):
        """验证手机号和密码是否匹配"""
        if qitian:
            user = cls.get_by_qitian(qitian)
        else:
            user = cls.get_by_phone(phone)

        salt, hashed_password = User.hash_password(password, user.salt)
        if hashed_password == user.password:
            return user
        raise UserErrors.PASSWORD

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

    def modify_avatar(self, avatar):
        """修改用户头像"""
        if self.avatar:
            from Base.qn import qn_public_manager
            qn_public_manager.delete_res(self.avatar)
        self.avatar = avatar
        self.save()

    def upload_verify_front(self, card_image_front):
        from Base.qn import qn_res_manager
        if self.card_image_front:
            qn_res_manager.delete_res(self.card_image_front)

        self.card_image_front = card_image_front
        self.save()
        qn_res_manager.get_resource_url(self.card_image_front + '-small')

    def upload_verify_back(self, card_image_back):
        from Base.qn import qn_res_manager
        if self.card_image_back:
            qn_res_manager.delete_res(self.card_image_back)

        self.card_image_back = card_image_back
        self.save()
        qn_res_manager.get_resource_url(self.card_image_back + '-small')

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
                self.exist_with_qitian(qitian)
                self.qitian = qitian
                self.qitian_modify_time += 1
        self.nickname = nickname
        self.description = description
        self.birthday = birthday
        self.save()

    def update_card_info(self, real_name, male, idcard, birthday):
        self.real_name = real_name
        self.male = male
        self.idcard = idcard
        self.birthday = birthday
        try:
            self.save()
        except Exception as err:
            return IDCardErrors.AUTO_VERIFY_FAILED(debug_message=err)

    def update_verify_status(self, status):
        self.verify_status = status
        self.save()

    def update_verify_type(self, verify_type):
        self.real_verify_type = verify_type
        self.save()

    def developer(self):
        self.is_dev = True
        self.save()

#
# class UserP:
#     birthday, password, nickname, description, qitian, idcard, male, real_name = User.P(
#         'birthday', 'password', 'nickname', 'description', 'qitian', 'idcard', 'male',
#         'real_name')
#
#     user = P('user_id', '用户唯一ID', 'user').process(User.get_by_str_id)
#     back = P('back', '侧别').process(int)
#
#     birthday.process(lambda s: datetime.datetime.strptime(s, '%Y-%m-%d').date(), begin=True)
