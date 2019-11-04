import datetime

from SmartDjango import E

from User.models import User


@E.register()
class PremiseCheckerError:
    REQUIRE_REAL_VERIFY = E("需要实名认证")
    CHECKER_NOT_FOUND = E("不存在的要求检测")
    DISALLOW_CHILD = E("需年满18周岁")


class PremiseChecker:
    @staticmethod
    def real_verified_checker(user):
        if user.verify_status != User.VERIFY_STATUS_DONE:
            raise PremiseCheckerError.REQUIRE_REAL_VERIFY

    @staticmethod
    def disallow_child_checker(user):
        if user.verify_status != User.VERIFY_STATUS_DONE:
            raise PremiseCheckerError.REQUIRE_REAL_VERIFY

        crt_date = datetime.datetime.now().date()
        if crt_date.year < user.birthday.year + 18:
            raise PremiseCheckerError.DISALLOW_CHILD
        elif crt_date.year > user.birthday.year + 18:
            return
        elif crt_date.month < user.birthday.month:
            raise PremiseCheckerError.DISALLOW_CHILD
        elif crt_date.month > user.birthday.month:
            return
        elif crt_date.day < user.birthday.day:
            raise PremiseCheckerError.DISALLOW_CHILD
