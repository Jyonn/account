import datetime

from smartdjango import Params, Validator

from User.models import User


class UserParams(metaclass=Params):
    model_class = User

    # birthday: Validator
    password: Validator
    nickname: Validator
    description: Validator
    desc: Validator
    qitian: Validator
    idcard: Validator
    male: Validator
    real_name: Validator

    user = Validator('user_id', verbose_name='用户ID', final_name='user').to(User.get_by_str_id)
    back = Validator('back', verbose_name='侧别').to(int)
    birthday = Validator('birthday').to(lambda s: datetime.datetime.strptime(s, '%Y-%m-%d').date())
