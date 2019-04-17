""" Adel Liu 180226

base子路由
"""
from django.urls import path

from Wechat.api_views import WechatAutoView, WechatConfigView

urlpatterns = [
    path('auto', WechatAutoView.as_view()),
    path('config', WechatConfigView.as_view())
]
