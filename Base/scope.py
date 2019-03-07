from App.models import Scope


class ScopeInstance:
    read_base_info = Scope.get_scope_by_name('readBaseInfo', default=None).body
    write_base_info = Scope.get_scope_by_name('writeBaseInfo', default=None).body
    send_email = Scope.get_scope_by_name('sendEmail', default=None).body
    send_mobile = Scope.get_scope_by_name('sendMobile', default=None).body
    read_app_list = Scope.get_scope_by_name('readMyAppList', default=None).body
    assert read_base_info
    assert write_base_info
    assert send_email
    assert send_mobile
    assert read_app_list
