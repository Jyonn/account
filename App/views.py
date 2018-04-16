from django.shortcuts import render
from django.views import View


class AppView(View):
    @staticmethod
    def apply(request):
        return render(request, 'app/apply.html')

    @staticmethod
    def info_modify(request, app_id):
        return render(request, 'app/info-modify.html', dict(app_id=app_id))
