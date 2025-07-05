""" 171203 Adel Liu """
from Config.models import Config, CI


def md5(s):
    """获取字符串的MD5"""
    import hashlib
    md5_ = hashlib.md5()
    md5_.update(s.encode())
    return md5_.hexdigest()


def sha1(s):
    import hashlib
    sha1_ = hashlib.sha1()
    sha1_.update(s.encode())
    return sha1_.hexdigest()


SECRET_KEY = Config.get_value_by_key(CI.PROJECT_SECRET_KEY)
JWT_ENCODE_ALGO = Config.get_value_by_key(CI.JWT_ENCODE_ALGO)
HOST = Config.get_value_by_key(CI.HOST)
