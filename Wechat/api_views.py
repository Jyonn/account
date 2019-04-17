from django.views import View

from Base.error import Error
from Base.response import error_response, response
from Base.valid_param import ValidParam
from Base.validator import require_param
from Base.weixin import Weixin


class WechatConfigView(View):
    @staticmethod
    @require_param([ValidParam('url', '链接')])
    def post(request):
        url = request.d.url
        ret = Weixin.get_config(url)
        if ret.error is not Error.OK:
            return error_response(ret)
        return response(ret.body)


class WechatAutoView(View):
    @staticmethod
    def get(request):
        ret = Weixin.update_access_token()
        if ret.error is not Error.OK:
            return error_response(ret)
        return response(ret.body)

