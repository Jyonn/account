from App.models import Scope


class ScopeInstance:
    r_base_info = Scope.get_scope_by_name('rBaseInfo', default=None).body
    w_base_info = Scope.get_scope_by_name('wBaseInfo', default=None).body
    send_email = Scope.get_scope_by_name('sendEmail', default=None).body
    send_mobile = Scope.get_scope_by_name('sendMobile', default=None).body
    r_app_list = Scope.get_scope_by_name('rAppList', default=None).body
    assert r_base_info
    assert w_base_info
    assert send_email
    assert send_mobile
    assert r_app_list
