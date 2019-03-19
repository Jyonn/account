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
    PASSWORD_CHANGED = E("密码已修改，请重新登录")
    INVALID_QITIAN = E("齐天号只能包含字母数字以及下划线")
    INVALID_PASSWORD = E("密码存在特殊字符")
    INVALID_USERNAME_FIRST = E("用户名首字符只能是字母")
    INVALID_USERNAME = E("用户名只能包含字母数字和下划线")
    UNAUTH_CALLBACK = E("未经授权的回调函数")
    PHONE_EXIST = E("手机号已注册")
    JWT_EXPIRED = E("身份认证过期，请重新登录")
    ERROR_JWT_FORMAT = E("身份认证错误，请登录")
    JWT_PARAM_INCOMPLETE = E("身份认证缺少参数，请登录")
    REQUIRE_DICT = E("需要字典数据")
    ERROR_CREATE_USER = E("存储用户错误")
    ERROR_PASSWORD = E("密码错误")
    NOT_FOUND_USER = E("不存在的用户")

    AES_ENCRYPT_ERROR = E("AES加密失败")
    AES_DECRYPT_ERROR = E("AES解密失败")

    GET_CAPTCHA_ERROR = E("获取验证码失败")
    CAPTCHA_EXPIRED = E("验证码过期，请重试")
    ERROR_CAPTCHA = E("验证失败")
    ERROR_CREATE_SCOPE = E("创建权限错误")
    NOT_FOUND_APP = E("不存在的应用")
    ERROR_CREATE_APP = E("创建应用错误")
    EXIST_APP_NAME = E("已存在此应用名")
    NOT_FOUND_SCOPE = E("不存在的权限")
    APP_NOT_BELONG = E("不是你的应用")
    ERROR_MODIFY_APP = E("修改应用信息错误")
    ERROR_INTERACTION = E("操作失败，请再试一次")
    ERROR_SESSION = E("会话错误，请刷新重试")
    ERROR_TOKEN_TYPE = E("错误的Token类型，登录失败")
    NOT_FOUND_USER_APP = E("请仔细阅读应用所需权限")
    ERROR_BIND_USER_APP = E("无法绑定应用")
    REQUIRE_AUTH_CODE = E("需要身份认证code")
    APP_FIELD_CHANGE = E("应用信息发生变化")
    NEW_AUTH_CODE_CREATED = E("授权失效")
    APP_UNBINDED = E("应用被用户解绑")
    SCOPE_NOT_SATISFIED = E("没有获取权限：")
    DENY_ALL_AUTH_TOKEN = E("拒绝第三方认证请求")
    ERROR_APP_SECRET = E("错误的应用密钥")
    QITIAN_EXIST = E("已存在此齐天号")

    SCORE_REFRESHED = E("频率分数已经刷新")
    ERROR_CREATE_CONFIG = E("创建配置错误")

    ERROR_MARK = E("评分失败")
    ERROR_DATE_FORMAT = E("日期格式错误")
    ERROR_BIRTHDAY_FORMAT = E("错误的生日时间")
    NOT_FOUND_PREMISE = E("不存在的要求")
    ERROR_CREATE_PREMISE = E("创建要求错误")

    SEND_EMAIL_ERROR = E("邮件发送错误")
    EMAIL_NOT_EXIST = E("不存在邮箱")
    ILLEGAL_ACCESS_RIGHT = E("非法访问权限")

    IDCARD_DETECT_ERROR = E("身份证自动验证错误")
    REAL_VERIFIED = E("已实名认证")


ERROR_DICT = dict()
REVERSED_ERROR_DICT = dict()
for k in Error.__dict__:
    if k[0] != '_':
        e = getattr(Error, k)
        if isinstance(e, E):
            ERROR_DICT[k] = dict(eid=e.eid, msg=e.msg)
            REVERSED_ERROR_DICT[e.eid] = k
