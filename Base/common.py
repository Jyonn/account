""" 171203 Adel Liu """

DEBUG = True


def deprint(*args):
    """
    系统处于调试状态时输出数据
    """
    if DEBUG:
        print(*args)


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


def get_client_ip(request):
    if 'HTTP_X_FORWARDED_FOR' in request.META:
        return request.META['HTTP_X_FORWARDED_FOR']
    else:
        return request.META['REMOTE_ADDR']
