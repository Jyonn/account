from smartdjango import Error, Code


@Error.register
class AppErrors:
    PREMISE_NOT_FOUND = Error("不存在的要求", code=Code.NotFound)
    CREATE_PREMISE = Error("创建要求错误", code=Code.InternalServerError)

    CREATE_SCOPE = Error("创建权限错误", code=Code.InternalServerError)
    SCOPE_NOT_FOUND = Error("不存在的权限", code=Code.NotFound)

    APP_NOT_FOUND = Error("不存在的应用", code=Code.NotFound)
    CREATE_APP = Error("创建应用错误", code=Code.InternalServerError)
    EXIST_APP_NAME = Error("已存在此应用名", code=Code.BadRequest)
    APP_NOT_BELONG = Error("不是你的应用", code=Code.BadRequest)
    MODIFY_APP = Error("修改应用信息错误", code=Code.InternalServerError)
    USER_FULL = Error("用户注册数量达到上限", code=Code.BadRequest)
    APP_NAME_TOO_SHORT = Error("应用名不应少于 {length} 个字符", code=Code.BadRequest)

    USER_APP_NOT_FOUND = Error("请仔细阅读应用所需权限", code=Code.BadRequest)
    BIND_USER_APP = Error("无法绑定应用", code=Code.InternalServerError)
    APP_NOT_BOUND = Error("应用被用户解绑", code=Code.Unauthorized)

    SCORE_REFRESHED = Error("频率分数已经刷新", code=Code.BadRequest)

    MARK = Error("评分失败", code=Code.InternalServerError)
    APP_SECRET = Error("错误的应用密钥", code=Code.Unauthorized)

    ILLEGAL_ACCESS_RIGHT = Error("非法访问权限", code=Code.Unauthorized)


class PremiseValidator:
    MAX_NAME_LENGTH = 20
    MAX_DESC_LENGTH = 20
    MAX_DETAIL_LENGTH = 100


class ScopeValidator:
    MAX_NAME_LENGTH = 20
    MAX_DESC_LENGTH = 20
    MAX_DETAIL_LENGTH = 100


class AppValidator:
    MAX_NAME_LENGTH = 32
    MIN_NAME_LENGTH = 2
    MAX_ID_LENGTH = 32
    DEFAULT_ID_LENGTH = 8
    MAX_SECRET_LENGTH = 32
    MAX_REDIRECT_URI_LENGTH = 512
    MAX_TEST_REDIRECT_URI_LENGTH = 512
    MAX_DESC_LENGTH = 32
    MAX_LOGO_LENGTH = 1024

    @classmethod
    def name(cls, value):
        if len(value) < cls.MIN_NAME_LENGTH:
            raise AppErrors.APP_NAME_TOO_SHORT(length=cls.MIN_NAME_LENGTH)


class UserAppValidator:
    MAX_USER_APP_ID_LENGTH = 16
    MAX_LAST_USER_APP_ID_LENGTH = 20
    MAX_LAST_SCORE_CHANGED_TIME_LENGTH = 20
