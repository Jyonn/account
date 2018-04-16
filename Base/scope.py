from App.models import Scope


class ScopeInstance:
    r_base_info = Scope.get_scope_by_name('rBaseInfo', default=None).body
    assert r_base_info
