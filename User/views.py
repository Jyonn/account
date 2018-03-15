from django.shortcuts import render

from Base.captcha import Captcha


class UserView:
    @staticmethod
    def register(request):
        o_captcha = Captcha.get(request)
        return render(request, 'user/register.html', dict(captcha=o_captcha))
