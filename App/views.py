from django.shortcuts import render
from django.views import View


class AppView(View):
    @staticmethod
    def apply(request):
        return render(request, 'app/apply.html')
