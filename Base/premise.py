from Base.error import Error
from Base.response import Ret
from User.models import User


class PremiseChecker:
    @staticmethod
    def real_verified_checker(o_user):
        if not isinstance(o_user, User):
            return Ret(Error.STRANGE)
