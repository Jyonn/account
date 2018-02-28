"""171203 Adel Liu

第一次使用jwt身份认证技术
"""
import datetime

import jwt

from Base.common import deprint
from Base.error import Error
from Base.response import Ret
from account.settings import SECRET_KEY, JWT_ENCODE_ALGO


def jwt_e(dict_, replace=True, expire_second=7 * 60 * 60 * 24):
    """
    jwt签名加密
    :param replace: 如果dict_中存在ctime或expire是否替换
    :param dict_: 被加密的字典数据
    :param expire_second: 过期时间
    """
    if not isinstance(dict_, dict):
        return Ret(Error.STRANGE)
    if replace or 'ctime' not in dict_.keys():
        dict_['ctime'] = datetime.datetime.now().timestamp()
    if replace or 'expire' not in dict_.keys():
        dict_['expire'] = expire_second
    encode_str = jwt.encode(dict_, SECRET_KEY, algorithm=JWT_ENCODE_ALGO).decode()
    return Ret((encode_str, dict_))


def jwt_d(str_):
    """
    jwt签名解密
    :param str_: 被加密的字符串
    """
    if not isinstance(str_, str):
        return Ret(Error.STRANGE)
    try:
        dict_ = jwt.decode(str_, SECRET_KEY, JWT_ENCODE_ALGO)
    except jwt.DecodeError as err:
        deprint(str(err))
        return Ret(Error.ERROR_JWT_FORMAT)
    if 'expire' not in dict_.keys() \
            or 'ctime' not in dict_.keys() \
            or not isinstance(dict_['ctime'], float) \
            or not isinstance(dict_['expire'], int):
        return Ret(Error.JWT_PARAM_INCOMPLETE)
    if datetime.datetime.now().timestamp() > dict_['ctime'] + dict_['expire']:
        return Ret(Error.JWT_EXPIRED)
    return Ret(dict_)
