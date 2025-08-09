from smartdjango import Params, Validator, ListValidator

from App.models import App, Scope, Premise, UserApp


class AppParams(metaclass=Params):
    model_class = App

    name: Validator
    info: Validator
    desc: Validator
    redirect_uri: Validator
    test_redirect_uri: Validator
    secret: Validator
    max_user_num: Validator

    scopes = ListValidator('scopes', '应用权限列表').element(Validator().to(Scope.get_by_name))
    premises = ListValidator('premises', '应用要求列表').element(Validator().to(Premise.get_by_name))

    app = Validator('app_id', '应用ID', 'app').to(App.get_by_id)
    user_app = Validator('user_app_id', '用户绑定应用ID', 'user_app').to(UserApp.get_by_id)
