""" Adel Liu 180226

base子路由
"""
from django.urls import path

from Base import views


urlpatterns = [
    path('regions', views.Region.as_view()),
    path('recaptcha', views.ReCaptchaView.as_view()),
]
