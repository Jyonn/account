from django.shortcuts import render
from django.views import View

from App.models import App
from Base.validator import require_param
from Base.error import Error
from Base.response import error_response


class OAuthView(View):
    @staticmethod
    @require_param(q=['app_id'])
    def oauth(request):
        """GET /oauth?app_id=:app_id

        授权应用并使用应用
        """

        app_id = request.d.app_id
        ret = App.get_app_by_id(app_id)
        if ret.error is not Error.OK:
            return error_response(ret)

        o_app = ret.body
        if not isinstance(o_app, App):
            return error_response(Error.STRANGE)

        return render(request, 'user/oauth.html', dict(app_info=o_app.to_dict()))
