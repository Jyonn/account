""" Adel Liu 180228

用户API子路由
"""
from django.urls import path

from User.api_views import UserView, TokenView, AvatarView

urlpatterns = [
    path('', UserView.as_view()),
    # path('@<str:qitian>', QitianView.as_view()),
    path('token', TokenView.as_view()),
    path('avatar', AvatarView.as_view()),
]
