""" 171203 Adel Liu

弃用http.require_POST和http.require_GET
将require_POST和require_params合二为一
把最终参数字典存储在request.d中
"""

import base64
import json
from functools import wraps

from django.db import models
from django.http import HttpRequest

from Base.common import deprint
from Base.error import Error
from Base.jtoken import JWType
from Base.param import Param
from Base.response import Ret, error_response
from Base.valid_param import ValidParam


def validate_params(r_param_valid_list, g_params):
    """ 验证参数

    [
        ('a', '[a-z]+'),
        'b',
        ('c', valid_c_func),
        ('d', valid_d_func, default_d_value)
        {
            "value": "e",
            "func": valid_e_func,
            "default": True,
            "default_value": default_e_value,
            "process": process_e_value (str to int),
            "readable": using by response error
        },
        class ValidParam "f"
    ]
    """
    import re

    if not r_param_valid_list:
        return Ret()
    for r_param_valid in r_param_valid_list:
        # has_default_value = False
        # default_value = None  # 默认值
        
        # valid_method = None  # 验证参数的方式（如果是字符串则为正则匹配，如果是函数则带入函数，否则忽略）
        # process = None
        # readable = None

        if isinstance(r_param_valid, str):  # 如果rpv只是个字符串，则符合例子中的'b'情况
            current_param = ValidParam(r_param_valid)
        elif isinstance(r_param_valid, tuple):  # 如果rpv是tuple，则依次为变量名、验证方式、默认值 'c'
            if not r_param_valid:  # 忽略
                continue
            current_param = ValidParam(r_param_valid[0])  # 得到变量名
            if len(r_param_valid) > 1:
                current_param.fc(r_param_valid[1])  # 得到验证方式
                if len(r_param_valid) > 2:  # d
                    # has_default_value = True
                    g_params.setdefault(current_param.param, r_param_valid[2])
        elif isinstance(r_param_valid, dict):  # 'e'
            current_param = ValidParam(r_param_valid.get('value', None))
            if current_param.param is None:
                continue
            current_param.fc(r_param_valid.get('func', None))
            default = r_param_valid.get('default', False)
            default_value = r_param_valid.get('default_value', None)
            if default:
                g_params.setdefault(current_param.param, default_value)
            current_param.p(r_param_valid.get('process', None))
            current_param.r(r_param_valid.get('readable', None))
        elif isinstance(r_param_valid, ValidParam):  # 'f'
            current_param = r_param_valid
            if current_param.param is None:
                continue
            if current_param.default:
                g_params.setdefault(current_param.param, current_param.default_value)
        else:  # 忽略
            continue

        current_param.readable = current_param.readable or current_param.param

        if current_param.param not in g_params:  # 如果传入数据中没有变量名
            return Ret(Error.REQUIRE_PARAM, append_msg=current_param.readable)  # 报错

        req_value = g_params[current_param.param]

        if isinstance(current_param.func, str):
            if re.match(current_param.func, req_value) is None:
                return Ret(Error.ERROR_PARAM_FORMAT, append_msg=current_param.readable)
        elif callable(current_param.func):
            try:
                ret = current_param.func(req_value)
                if ret.error is not Error.OK:
                    return ret
            except Exception as err:
                deprint(str(err))
                return Ret(Error.ERROR_VALIDATION_FUNC)
        if current_param.process and callable(current_param.process):
            try:
                g_params[current_param.param] = current_param.process(req_value)
            except Exception as err:
                deprint(str(err))
                return Ret(Error.ERROR_PROCESS_FUNC)
    return Ret(g_params)


def field_validator(dict_, cls):
    """
    针对model的验证函数
    事先需要FIELD_LIST存放需要验证的属性
    需要L字典存放CharField类型字段的最大长度
    可选MIN_L字典存放CharField字段最小长度
    可选创建_valid_<param>函数进行自校验
    """
    field_list = getattr(cls, 'FIELD_LIST', None)
    if field_list is None:
        return Ret(Error.ERROR_VALIDATION_FUNC, append_msg='，不存在FIELD_LIST')
    _meta = getattr(cls, '_meta', None)
    if _meta is None:
        return Ret(Error.ERROR_VALIDATION_FUNC, append_msg='，不是Django的models类')
    len_list = getattr(cls, 'L', None)
    if len_list is None:
        return Ret(Error.ERROR_VALIDATION_FUNC, append_msg='，不存在长度字典L')
    min_len_list = getattr(cls, 'MIN_L', None)

    for k in dict_.keys():
        if k in getattr(cls, 'FIELD_LIST'):
            if dict_[k] is None:
                continue
            if isinstance(_meta.get_field(k), models.CharField):
                try:
                    if len(dict_[k]) > len_list[k]:
                        return Ret(
                            Error.ERROR_PARAM_FORMAT,
                            append_msg='，%s的长度不应超过%s个字符' % (k, len_list[k])
                        )
                    if min_len_list and k in min_len_list and len(dict_[k]) < min_len_list[k]:
                        return Ret(
                            Error.ERROR_PARAM_FORMAT,
                            append_msg=',%s的长度不应少于%s个字符' % (k, min_len_list[k])
                        )
                except TypeError as err:
                    deprint(str(err))
                    return Ret(Error.ERROR_PARAM_FORMAT, append_msg="，%s不是字符串" % k)

        tuple_name = '%s_TUPLE' % k.upper()
        tuple_ = getattr(cls, tuple_name, None)
        if tuple_ is not None and isinstance(tuple_, tuple):
            flag = False
            for item in tuple_:
                if not isinstance(item, tuple):
                    return Ret(Error.ERROR_TUPLE_FORMAT, append_msg='（%s）' % tuple_name)
                if dict_[k] == item[0]:
                    flag = True
            if not flag:
                return Ret(Error.ERROR_PARAM_FORMAT, append_msg='，%s的值应该在%s之中' % (k, tuple_name))
        valid_func = getattr(cls, '_valid_%s' % k, None)
        if valid_func is not None and callable(valid_func):
            # print('_valid_', k)
            ret = valid_func(dict_[k])
            if ret.error is not Error.OK:
                return ret
    return Ret()


def require_scope(scope_list=list(), deny_all_auth_token=False, allow_no_login=False):
    def decorator(func):
        """decorator"""
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            type_ = getattr(request, 'type_', None)
            if not type_:
                if allow_no_login:
                    return func(request, *args, **kwargs)
                else:
                    return error_response(Error.REQUIRE_LOGIN)

            if type_ != JWType.AUTH_TOKEN:
                return func(request, *args, **kwargs)

            if deny_all_auth_token:
                return error_response(Error.DENY_ALL_AUTH_TOKEN)
            o_app = request.user_app.app

            from App.models import App, Scope
            if not isinstance(o_app, App):
                deprint('Base-validator-scope_validator-o_app')
                return error_response(Error.STRANGE)

            if not isinstance(scope_list, list):
                deprint('Base-validator-scope_validator-scope_list')
                return error_response(Error.STRANGE)
            for o_scope in scope_list:
                if not isinstance(o_scope, Scope):
                    decorator_generator('Base-validator-scope_validator-o_scope')
                    return error_response(Error.STRANGE)
                if o_scope not in o_app.scopes.all():
                    return error_response(Error.SCOPE_NOT_SATISFIED, append_msg=o_scope.desc)
            return func(request, *args, **kwargs)
        return wrapper
    return decorator


def require_method(method, r_params=None, decode=True):
    """generate decorator, validate func with proper method and params"""
    def decorator(func):
        """decorator"""
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            """wrapper"""
            if not isinstance(request, HttpRequest):
                return error_response(Error.STRANGE)
            if request.method != method:
                return error_response(Error.ERROR_METHOD, append_msg='，需要%s请求' % method)
            if request.method == "GET":
                request.DICT = request.GET.dict()
            else:
                try:
                    request.DICT = json.loads(request.body.decode())
                except json.JSONDecodeError as err:
                    deprint(str(err))
                    request.DICT = {}
            if decode:
                for k in request.DICT.keys():
                    import binascii
                    try:
                        base64.decodebytes(bytes(request.DICT[k], encoding='utf8')).decode()
                    except binascii.Error as err:
                        deprint(str(err))
                        return error_response(Error.REQUIRE_BASE64)
            ret = validate_params(r_params, request.DICT)
            if ret.error is not Error.OK:
                return error_response(ret)
            request.d = Param(ret.body)
            return func(request, *args, **kwargs)

        return wrapper
    return decorator


def require_post(r_params=None, decode=False):
    """decorator, require post method"""
    return require_method('POST', r_params, decode)


def require_get(r_params=None, decode=False):
    """decorator, require get method"""
    return require_method('GET', r_params, decode)


def require_put(r_params=None, decode=False):
    """decorator, require put method"""
    return require_method('PUT', r_params, decode)


def require_delete(r_params=None, decode=False):
    """decorator, require delete method"""
    return require_method('DELETE', r_params, decode)


def require_json(func):
    """把request.body的内容反序列化为json"""
    @wraps(func)
    def wrapper(request, *args, **kwargs):
        """wrapper"""
        if request.body:
            try:
                request.DICT = json.loads(request.body.decode())
            except json.JSONDecodeError as err:
                deprint(str(err))
            return func(request, *args, **kwargs)
        return error_response(Error.REQUIRE_JSON)
    return wrapper


def decorator_generator(verify_func):
    """装饰器生成器"""
    def decorator(func):
        """decorator"""
        def wrapper(request, *args, **kwargs):
            """wrapper, using verify_func to verify"""
            ret = verify_func(request)
            if ret.error is not Error.OK:
                return error_response(ret)
            return func(request, *args, **kwargs)
        return wrapper
    return decorator


def require_login_func(request):
    """需要登录

    并根据传入的token获取user
    """
    jwt_str = request.META.get('HTTP_TOKEN')
    if jwt_str is None:
        return Ret(Error.REQUIRE_LOGIN)
    from Base.jtoken import jwt_d

    ret = jwt_d(jwt_str)
    if ret.error is not Error.OK:
        return ret
    dict_ = ret.body

    ctime = dict_.get('ctime')
    if not ctime:
        deprint('Base-validator-require_login_func-dict.get(ctime)')
        return Ret(Error.STRANGE)

    type_ = dict_.get('type')
    if not type_:
        deprint('Base-validator-require_login_func-dict.get(type)')
        return Ret(Error.STRANGE)

    if type_ == JWType.LOGIN_TOKEN:
        user_id = dict_.get("user_id")
        if not user_id:
            deprint('Base-validator-require_login_func-dict.get(user_id)')
            return Ret(Error.STRANGE)

        from User.models import User
        ret = User.get_user_by_str_id(user_id)
        if ret.error is not Error.OK:
            return ret
        o_user = ret.body
        if not isinstance(o_user, User):
            return Ret(Error.STRANGE)
    elif type_ == JWType.AUTH_TOKEN:
        user_app_id = dict_.get('user_app_id')
        if not user_app_id:
            deprint('Base-validator-require_login_func-dict.get(user_app_id)')
            return Ret(Error.STRANGE)

        from App.models import UserApp
        ret = UserApp.get_user_app_by_user_app_id(user_app_id, check_bind=True)
        if ret.error is not Error.OK:
            return ret
        o_user_app = ret.body
        if not isinstance(o_user_app, UserApp):
            return Ret(Error.STRANGE)

        if float(o_user_app.app.field_change_time) > ctime:
            return Ret(Error.APP_FIELD_CHANGE)

        o_user = o_user_app.user
        request.user_app = o_user_app
    else:
        return Ret(Error.ERROR_TOKEN_TYPE)

    if float(o_user.pwd_change_time) > ctime:
        return Ret(Error.PASSWORD_CHANGED)

    request.user = o_user
    request.type_ = type_

    return Ret()


def maybe_login_func(request):
    """decorator, maybe require login"""
    require_login_func(request)
    return Ret()


def require_root_func(request):
    """decorator, require root login"""
    ret = require_login_func(request)
    if ret.error is not Error.OK:
        return ret
    o_user = request.user
    from User.models import User
    if not isinstance(o_user, User):
        return Ret(Error.STRANGE)
    if o_user.pk != User.ROOT_ID:
        return Ret(Error.REQUIRE_ROOT)
    return Ret()


require_login = decorator_generator(require_login_func)
maybe_login = decorator_generator(maybe_login_func)
require_root = decorator_generator(require_root_func)
