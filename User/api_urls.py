""" Adel Liu 180228

用户API子路由
"""
from django.urls import path

from User.api_views import UserView, TokenView, AvatarView, DevView, IDCardView, \
    VerifyView, UserPhoneView

urlpatterns = [
    path('', UserView.as_view()),
    path('token', TokenView.as_view()),
    path('avatar', AvatarView.as_view()),
    path('idcard', IDCardView.as_view()),
    path('verify', VerifyView.as_view()),
    path('dev', DevView.as_view()),
    path('phone', UserPhoneView.as_view()),
]
