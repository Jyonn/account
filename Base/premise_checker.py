import datetime

from Base.error import Error
from Base.response import Ret
from User.models import User


class PremiseChecker:
    @staticmethod
    def real_verified_checker(o_user):
        if not isinstance(o_user, User):
            return Ret(Error.STRANGE)
        if o_user.verify_status != User.VERIFY_STATUS_DONE:
            return Ret(Error.REQUIRE_REAL_VERIFY)
        return Ret()

    @staticmethod
    def disallow_child_checker(o_user):
        if not isinstance(o_user, User):
            return Ret(Error.STRANGE)
        if o_user.verify_status != User.VERIFY_STATUS_DONE:
            return Ret(Error.REQUIRE_REAL_VERIFY)

        crt_date = datetime.datetime.now().date()
        if crt_date.year < o_user.birthday.year + 18:
            return Ret(Error.DISALLOW_CHILD)
        elif crt_date.year > o_user.birthday.year + 18:
            return Ret()
        elif crt_date.month < o_user.birthday.month:
            return Ret(Error.DISALLOW_CHILD)
        elif crt_date.month > o_user.birthday.month:
            return Ret()
        elif crt_date.day < o_user.birthday.day:
            return Ret(Error.DISALLOW_CHILD)
        else:
            return Ret()
