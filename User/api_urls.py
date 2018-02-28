""" Adel Liu 180228

用户API子路由
"""
from django.urls import path

from User.router import rt_user, rt_user_token, rt_user_avatar, rt_username

urlpatterns = [
    path('', rt_user),
    path('@<str:username>', rt_username),
    path('token', rt_user_token),
    path('avatar', rt_user_avatar),
]
