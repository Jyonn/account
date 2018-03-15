""" Adel Liu 180226

base子路由
"""
from django.urls import path

from Base.api_views import ErrorView, RegionView, CaptchaView

urlpatterns = [
    path('errors', ErrorView.as_view()),
    path('regions', RegionView.as_view()),
    path('captcha', CaptchaView.as_view()),
]
