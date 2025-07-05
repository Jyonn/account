import datetime

from smartdjango import Error

from User.models import User


@Error.register
class PremiseCheckerErrors:
    REQUIRE_REAL_VERIFY = Error("需要实名认证")
    CHECKER_NOT_FOUND = Error("不存在的要求检测")
    DISALLOW_CHILD = Error("需年满18周岁")
    REQUIRE_CHINESE_PHONE = Error("仅支持中国大陆手机号注册用户")


class PremiseChecker:
    @staticmethod
    def real_verified_checker(user):
        if user.verify_status != User.VERIFY_STATUS_DONE:
            raise PremiseCheckerErrors.REQUIRE_REAL_VERIFY

    @staticmethod
    def disallow_child_checker(user):
        if user.verify_status != User.VERIFY_STATUS_DONE:
            raise PremiseCheckerErrors.REQUIRE_REAL_VERIFY

        crt_date = datetime.datetime.now().date()
        if crt_date.year < user.birthday.year + 18:
            raise PremiseCheckerErrors.DISALLOW_CHILD
        elif crt_date.year > user.birthday.year + 18:
            return
        elif crt_date.month < user.birthday.month:
            raise PremiseCheckerErrors.DISALLOW_CHILD
        elif crt_date.month > user.birthday.month:
            return
        elif crt_date.day < user.birthday.day:
            raise PremiseCheckerErrors.DISALLOW_CHILD

    @staticmethod
    def chinese_phone_checker(user):
        if not user.phone.startswith('+86'):
            raise PremiseCheckerErrors.REQUIRE_CHINESE_PHONE
