from App.models import Scope
from account.settings import PROJ_INIT


class ScopeInstance:
    if PROJ_INIT:
        read_base_info = \
            write_base_info = \
            send_email = \
            send_mobile = \
            read_app_list = \
            read_phone = 0
    else:
        read_base_info = Scope.get_by_name('readBaseInfo')
        write_base_info = Scope.get_by_name('writeBaseInfo')
        send_email = Scope.get_by_name('sendEmail')
        send_mobile = Scope.get_by_name('sendMobile')
        read_app_list = Scope.get_by_name('readMyAppList')
        read_phone = Scope.get_by_name('readPhone')
        assert read_base_info
        assert write_base_info
        assert send_email
        assert send_mobile
        assert read_app_list
        assert read_phone


SI = ScopeInstance
