""" Adel Liu 180228

用户API子路由
"""
from django.urls import path

from User import views

urlpatterns = [
    path('', views.UserView.as_view()),
    path('token', views.TokenView.as_view()),
    path('avatar', views.AvatarView.as_view()),
    path('idcard', views.IDCardView.as_view()),
    path('verify', views.VerifyView.as_view()),
    path('dev', views.DevView.as_view()),
    path('phone', views.UserPhoneView.as_view()),
]
