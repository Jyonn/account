from django.shortcuts import render

from Base.captcha import Captcha


class UserView:
    @staticmethod
    def register(request):
        o_captcha = Captcha.get(request)
        return render(request, 'user/register.html', dict(captcha=o_captcha))

    @staticmethod
    def center(request):
        return render(request, 'user/center.html')

    @staticmethod
    def bind_phone(request):
        o_captcha = Captcha.get(request)
        return render(request, 'user/bind-phone.html', dict(captcha=o_captcha))

    @staticmethod
    def config(request):
        return render(request, 'user/info-modify.html')

    @staticmethod
    def settings(request):
        return render(request, 'user/settings.html')