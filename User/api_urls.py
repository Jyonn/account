""" Adel Liu 180228

用户API子路由
"""
from django.urls import path

from User.api_views import UserView, TokenView, AvatarView, DevView, IDCardView, \
    VerifyView

urlpatterns = [
    path('', UserView.as_view()),
    # path('@<str:qitian>', QitianView.as_view()),
    path('token', TokenView.as_view()),
    path('avatar', AvatarView.as_view()),
    path('idcard', IDCardView.as_view()),
    path('verify', VerifyView.as_view()),
    path('dev', DevView.as_view()),

    # path('@set-unique-user-str-id', set_unique_user_str_id)
]
