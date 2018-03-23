from django.urls import path

from User.views import UserView as View

urlpatterns = [
    path('register', View.register, name="user-register"),
    path('center', View.center, name='user-center'),
    path('bind-phone', View.bind_phone, name='user-bind-phone'),
    path('info-modify', View.config, name='user-info-modify'),
    path('settings', View.settings, name='user-settings'),
    path('login', View.login, name='user-login'),
]
