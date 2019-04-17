from django.views import View

from Base.valid_param import ValidParam
from Base.validator import require_param
from Base.weixin import Weixin


class WechatConfigView(View):
    @staticmethod
    @require_param(q=[ValidParam('url', '链接')])
    def get(request):
        url = request.d.url
        return Weixin.get_config(url)


class WechatAutoView(View):
    @staticmethod
    def get(request):
        return Weixin.update_access_token()
