""" Adel Liu 180228

用户API子路由
"""
from django.urls import path

from User.api_views import UserView, UsernameView, TokenView, AvatarView

urlpatterns = [
    path('', UserView.as_view()),
    path('@<str:username>', UsernameView.as_view()),
    path('token', TokenView.as_view()),
    path('avatar', AvatarView.as_view()),
]
