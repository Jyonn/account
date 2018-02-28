from django.views import View

from Base import country
from Base.decorator import require_get
from Base.error import Error
from Base.response import response


class ErrorView(View):
    @staticmethod
    def get(request):
        return response(body=Error.get_error_dict())


class RegionView(View):
    @staticmethod
    def process_lang(lang):
        if lang not in ['cn', 'en']:
            return 'cn'
        return lang

    @staticmethod
    @require_get([{
        'value': 'lang',
        'default': True,
        'default_value': 'cn',
        'process': process_lang,
    }])
    def get(request):
        lang = request.d.lang
        lang_cn = lang == country.LANG_CN
        regions = [
            dict(
                num=c['num'],
                name=c['cname'] if lang_cn else c['ename']
            ) for c in country.countries
        ]
        return response(body=regions)
