from django.views import View

from Base.response import error_response
from Base.valid_param import ValidParam
from Base.validator import require_param
from Base.weixin import Weixin


class WechatConfigView(View):
    @staticmethod
    @require_param(q=[ValidParam('url', '链接')])
    def get(request):
        url = request.d.url
        ret = Weixin.get_config(url)
        return error_response(ret)


class WechatAutoView(View):
    @staticmethod
    def get(request):
        ret = Weixin.update_access_token()
        return error_response(ret)
