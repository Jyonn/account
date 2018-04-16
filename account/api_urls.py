""" Adel Liu 180111

API子路由
"""
from django.urls import path, include

urlpatterns = [
    path('user/', include('User.api_urls')),
    path('base/', include('Base.api_urls')),
    path('app/', include('App.api_urls')),
    path('oauth/', include('OAuth.api_urls')),
]
