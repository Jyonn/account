from django.views import View
from smartdjango import Validator, analyse

from Base.weixin import Weixin


class WechatConfigView(View):
    @analyse.body(Validator('url', '链接'))
    def post(self, request):
        url = request.body.url
        return Weixin.get_config(url)


class WechatAutoView(View):
    def get(self, request):
        return Weixin.update_access_token()
