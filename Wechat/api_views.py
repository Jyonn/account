from SmartDjango import Analyse, P
from django.views import View

from Base.weixin import Weixin


class WechatConfigView(View):
    @staticmethod
    @Analyse.r([P('url', '链接')])
    def post(request):
        url = request.d.url
        return Weixin.get_config(url)


class WechatAutoView(View):
    @staticmethod
    def get(request):
        return Weixin.update_access_token()
