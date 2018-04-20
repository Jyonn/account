"""171203 Adel Liu

即将使用web前端直接上传到七牛 而无需通过服务器 减小服务器压力
"""
import qiniu
import requests
from django.http import HttpRequest
from qiniu import urlsafe_base64_encode

from Base.common import deprint
from Base.error import Error
from Base.response import Ret
from Config.models import Config
from account.settings import HOST

ACCESS_KEY = Config.get_value_by_key('qiniu-access-key', 'YOUR-ACCESS-KEY').body
SECRET_KEY = Config.get_value_by_key('qiniu-secret-key', 'YOUR-SECRET-KEY').body
RES_BUCKET = Config.get_value_by_key('qiniu-res-bucket', 'YOUR-RES-BUCKET').body
PUBLIC_BUCKET = Config.get_value_by_key('qiniu-public-bucket', 'YOUR-PUBLIC-BUCKET').body

_AUTH = qiniu.Auth(access_key=ACCESS_KEY, secret_key=SECRET_KEY)
_HOST = HOST
_KEY_PREFIX = 'account/'

QINIU_MANAGE_HOST = "https://rs.qiniu.com"
RES_CDN_HOST = 'https://res.6-79.cn'
PUBLIC_CDN_HOST = 'https://image.6-79.cn'


class QN:
    def __init__(self, auth, bucket, cdn_host, public):
        self.auth = auth
        self.bucket = bucket
        self.cdn_host = cdn_host
        self.public = public

    def get_upload_token(self, key, policy):
        """
        获取七牛上传token
        :param policy: 上传策略
        :param key: 规定的键
        """
        key = _KEY_PREFIX + key
        return self.auth.upload_token(bucket=self.bucket, key=key, expires=3600, policy=policy), key

    def qiniu_auth_callback(self, request):
        """七牛callback认证校验"""
        if not isinstance(request, HttpRequest):
            return Ret(Error.STRANGE)
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        if auth_header is None:
            return Ret(Error.UNAUTH_CALLBACK)
        url = request.get_full_path()
        body = request.body
        verified = self.auth.verify_callback(auth_header, url, body, content_type='application/json')
        if not verified:
            return Ret(Error.UNAUTH_CALLBACK)
        return Ret()

    def get_resource_url(self, key, expires=3600):
        """获取资源链接"""
        url = '%s/%s' % (self.cdn_host, key)
        if self.public:
            return '%s%s' % (self.cdn_host, key)
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
            return Ret(Error.ERROR_REQUEST_QINIU)
        status = r.status_code
        r.close()
        if status == 200:
            return Ret()
        elif status == 401:
            return Ret(Error.QINIU_UNAUTHORIZED)
        else:
            deprint(status)
            return Ret(Error.FAIL_QINIU)

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


QN_RES_MANAGER = QN(_AUTH, RES_BUCKET, RES_CDN_HOST, public=False)
QN_PUBLIC_MANAGER = QN(_AUTH, PUBLIC_BUCKET, PUBLIC_CDN_HOST, public=True)
