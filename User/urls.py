""" Adel Liu 180228

用户API子路由
"""
from django.urls import path

from User import views

urlpatterns = [
    path('', views.UserV.as_view()),
    path('token', views.Token.as_view()),
    path('avatar', views.Avatar.as_view()),
    path('idcard', views.IDCardV.as_view()),
    path('verify', views.Verify.as_view()),
    path('dev', views.Dev.as_view()),
    path('phone', views.UserPhone.as_view()),
]
