import datetime
import re

from smartdjango import Error, Code


@Error.register
class UserErrors:
    CREATE_USER = Error("存储用户错误", code=Code.InternalServerError)
    PASSWORD = Error("密码错误", code=Code.Unauthorized)
    USER_NOT_FOUND = Error("不存在的用户", code=Code.NotFound)
    INVALID_QITIAN = Error("齐天号只能包含字母数字以及下划线", code=Code.BadRequest)
    INVALID_PASSWORD = Error("密码存在特殊字符", code=Code.BadRequest)
    INVALID_USERNAME_FIRST = Error("用户名首字符只能是字母", code=Code.BadRequest)
    INVALID_USERNAME = Error("用户名只能包含字母数字和下划线", code=Code.BadRequest)
    ERROR_DATE_FORMAT = Error("日期格式错误", code=Code.BadRequest)
    BIRTHDAY_FORMAT = Error("错误的生日时间", code=Code.BadRequest)
    PHONE_EXIST = Error("手机号已注册", code=Code.BadRequest)
    QITIAN_EXIST = Error("已存在此齐天号", code=Code.BadRequest)
    QITIAN_TOO_SHORT = Error("齐天号长度不能小于 {length}", code=Code.BadRequest)
    PASSWORD_TOO_SHORT = Error("密码长度不能小于 {length}", code=Code.BadRequest)


class UserValidator:
    DEFAULT_USER_STR_ID_LENGTH = 6
    DEFAULT_QITIAN_LENGTH = 8
    DEFAULT_SALT_LENGTH = 6
    MAX_USER_STR_ID_LENGTH = 32
    MAX_QITIAN_LENGTH = 20
    MIN_QITIAN_LENGTH = 4
    MAX_PHONE_LENGTH = 20
    MAX_PASSWORD_LENGTH = 32
    MIN_PASSWORD_LENGTH = 6
    MAX_SALT_LENGTH = 10
    MAX_AVATAR_LENGTH = 1024
    MAX_NICKNAME_LENGTH = 10
    MAX_DESCRIPTION_LENGTH = 20
    MAX_REAL_NAME_LENGTH = 32
    MAX_IDCARD_LENGTH = 18
    MAX_CARD_IMAGE_FRONT_LENGTH = 1024
    MAX_CARD_IMAGE_BACK_LENGTH = 1024

    @staticmethod
    def qitian(value):
        """验证齐天号合法"""
        valid_chars = '^[A-Za-z0-9_]{4,20}$'
        if re.match(valid_chars, value) is None:
            raise UserErrors.INVALID_QITIAN

        if len(value) < UserValidator.MIN_QITIAN_LENGTH:
            raise UserErrors.QITIAN_TOO_SHORT(length=UserValidator.MIN_QITIAN_LENGTH)

    @staticmethod
    def password(value):
        """验证密码合法"""
        valid_chars = '^[A-Za-z0-9!@#$%^&*()_+-=,.?;:]{6,16}$'
        if re.match(valid_chars, value) is None:
            raise UserErrors.INVALID_PASSWORD

        if len(value) < UserValidator.MIN_PASSWORD_LENGTH:
            raise UserErrors.PASSWORD_TOO_SHORT(length=UserValidator.MIN_PASSWORD_LENGTH)

    @staticmethod
    def birthday(value):
        if value > datetime.datetime.now().date():
            raise UserErrors.BIRTHDAY_FORMAT
