""" 180226 Adel Liu

错误表，在编码时不断添加
自动生成eid
"""


class E:
    _error_id = 0

    def __init__(self, msg):
        self.eid = E._error_id
        self.msg = msg
        E._error_id += 1


class Error:
    OK = E("没有错误")
    ERROR_NOT_FOUND = E("不存在的错误")
    REQUIRE_PARAM = E("缺少参数")
    REQUIRE_JSON = E("需要JSON数据")
    REQUIRE_LOGIN = E("需要登录")
    STRANGE = E("未知错误")
    REQUIRE_BASE64 = E("参数需要base64编码")
    ERROR_PARAM_FORMAT = E("错误的参数格式")
    ERROR_METHOD = E("错误的HTTP请求方法")
    ERROR_VALIDATION_FUNC = E("错误的参数验证函数")
    REQUIRE_ROOT = E("需要管理员登录")
    ERROR_TUPLE_FORMAT = E("属性元组格式错误")
    ERROR_PROCESS_FUNC = E("参数预处理函数错误")
    BETA_CODE_ERROR = E("内测码错误")
    
    NOT_FOUND_CONFIG = E("不存在的配置")
    FAIL_QINIU = E("未知原因导致的七牛端操作错误")
    QINIU_UNAUTHORIZED = E("七牛端身份验证错误")
    ERROR_REQUEST_QINIU = E("七牛请求错误")
    PASSWORD_CHANGED = E("密码已改变，需要重新获取token")
    INVALID_PASSWORD = E("密码只能包含字母数字以及“!@#$%^&*()_+-=,.?;:”")
    INVALID_USERNAME_FIRST = E("用户名首字符只能是字母")
    INVALID_USERNAME = E("用户名只能包含字母数字和下划线")
    UNAUTH_CALLBACK = E("未经授权的回调函数")
    USERNAME_EXIST = E("已存在的用户名")
    JWT_EXPIRED = E("身份认证过期")
    ERROR_JWT_FORMAT = E("身份认证token错误")
    JWT_PARAM_INCOMPLETE = E("身份认证token缺少参数")
    REQUIRE_DICT = E("需要字典数据")
    ERROR_CREATE_USER = E("存储用户错误")
    ERROR_PASSWORD = E("错误的用户名或密码")
    NOT_FOUND_USER = E("不存在的用户")

    GET_CAPTCHA_ERROR = E("获取验证码失败")
    CAPTCHA_EXPIRED = E("验证码过期")
    ERROR_CAPTCHA = E("错误的验证码")
    ERROR_CREATE_SCOPE = E("创建权限错误")
    NOT_FOUND_APP = E("不存在的应用")
    ERROR_CREATE_APP = E("创建应用错误")
    EXIST_APP_NAME = E("已存在的应用名")
    NOT_FOUND_SCOPE = E("不存在的权限")
    APP_NOT_BELONG = E("不是你的应用")
    ERROR_MODIFY_APP = E("修改应用信息错误")

    @classmethod
    def get_error_dict(cls):
        error_dict = dict()
        for k in cls.__dict__:
            if k[0] != '_':
                e = getattr(cls, k)
                if isinstance(e, E):
                    error_dict[k] = dict(eid=e.eid, msg=e.msg)
        return error_dict
