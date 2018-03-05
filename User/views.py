from django.shortcuts import render


class UserView:
    @staticmethod
    def register(request):
        return render(request, 'base.html')
