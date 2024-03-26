"""171203 Adel Liu

即将使用web前端直接上传到七牛 而无需通过服务器 减小服务器压力
"""
import qiniu
import requests
from SmartDjango import E
from django.http import HttpRequest
from qiniu import urlsafe_base64_encode

from Base.common import HOST
from Config.models import Config, CI
from account.settings import PROJ_INIT

ACCESS_KEY = Config.get_value_by_key(CI.QINIU_ACCESS_KEY)
SECRET_KEY = Config.get_value_by_key(CI.QINIU_SECRET_KEY)
RES_BUCKET = Config.get_value_by_key(CI.RES_BUCKET)
PUBLIC_BUCKET = Config.get_value_by_key(CI.PUBLIC_BUCKET)
RES_CDN_HOST = Config.get_value_by_key(CI.RES_CDN_HOST)
PUBLIC_CDN_HOST = Config.get_value_by_key(CI.PUBLIC_CDN_HOST)

if PROJ_INIT:
    _AUTH = None
else:
    _AUTH = qiniu.Auth(access_key=ACCESS_KEY, secret_key=SECRET_KEY)
_HOST = HOST
_KEY_PREFIX = 'account/'

QINIU_MANAGE_HOST = "https://rs.qiniu.com"


@E.register()
class QNError:
    REQUEST_QINIU = E("七牛请求错误")
    QINIU_UNAUTHORIZED = E("七牛端身份验证错误")
    FAIL_QINIU = E("未知原因导致的七牛端操作错误")
    UNAUTH_CALLBACK = E("未经授权的回调函数")


class QnManager:
    def __init__(self, auth, bucket, cdn_host, public):
        self.auth = auth
        self.bucket = bucket
        self.cdn_host = cdn_host
        self.public = public

    @staticmethod
    def encode_key(key):
        key = key.replace('@', '@@')
        key = key.replace('$', '@S')
        return key

    @staticmethod
    def decode_key(key: str):
        new_key = ''
        while True:
            p_at = key.find('@')
            if p_at == -1:
                new_key += key
                break
            new_key += key[:p_at]
            if key[p_at + 1] == '@':
                new_key += '@'
            elif key[p_at + 1] == 'S':
                new_key += '$'
            else:
                pass
            key = key[p_at+2:]

        return new_key

    def get_upload_token(self, key, policy):
        """
        获取七牛上传token
        :param policy: 上传策略
        :param key: 规定的键
        """
        key = _KEY_PREFIX + key
        return self.auth.upload_token(bucket=self.bucket, key=key, expires=3600, policy=policy), key

    def auth_callback(self, request: HttpRequest):
        """七牛callback认证校验"""
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        if auth_header is None:
            raise QNError.UNAUTH_CALLBACK
        url = request.get_full_path()
        body = request.body
        verified = self.auth.verify_callback(auth_header, url, body,
                                             content_type='application/json')
        if not verified:
            raise QNError.UNAUTH_CALLBACK

    def get_resource_url(self, key, expires=3600, small=False):
        """获取资源链接"""
        url = '%s/%s' % (self.cdn_host, key)
        if small:
            return '%s-small' % url
        if self.public:
            return url
        else:
            return self.auth.private_download_url(url, expires=expires)

    @staticmethod
    def deal_manage_res(target, access_token):
        url = '%s%s' % (QINIU_MANAGE_HOST, target)
        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'QBox %s' % access_token,
        }

        try:
            r = requests.post(url, headers=headers)
        except requests.exceptions.RequestException:
            raise QNError.REQUEST_QINIU
        status = r.status_code
        r.close()
        if status == 200:
            return
        elif status == 401:
            raise QNError.QINIU_UNAUTHORIZED
        else:
            raise QNError.FAIL_QINIU('状态错误%s' % status)

    def delete_res(self, key):
        entry = '%s:%s' % (self.bucket, key)
        encoded_entry = urlsafe_base64_encode(entry)
        target = '/delete/%s' % encoded_entry
        access_token = self.auth.token_of_request(target, content_type='application/json')
        return self.deal_manage_res(target, access_token)

    def move_res(self, key, new_key):
        entry = '%s:%s' % (self.bucket, key)
        encoded_entry = urlsafe_base64_encode(entry)
        new_entry = '%s:%s' % (self.bucket, new_key)
        encoded_new_entry = urlsafe_base64_encode(new_entry)
        target = '/move/%s/%s' % (encoded_entry, encoded_new_entry)
        access_token = self.auth.token_of_request(target, content_type='application/json')
        return self.deal_manage_res(target, access_token)


qn_res_manager = QnManager(_AUTH, RES_BUCKET, RES_CDN_HOST, public=False)
qn_public_manager = QnManager(_AUTH, PUBLIC_BUCKET, PUBLIC_CDN_HOST, public=True)
