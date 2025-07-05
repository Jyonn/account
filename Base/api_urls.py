""" Adel Liu 180226

base子路由
"""
from django.urls import path

from Base import views


urlpatterns = [
    path('errors', views.ErrorView.as_view()),
    path('regions', views.Region.as_view()),
    path('recaptcha', views.ReCaptchaView.as_view()),
]
