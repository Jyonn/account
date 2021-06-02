""" Adel Liu 180111

API子路由
"""
from django.urls import path, include

urlpatterns = [
    path('user/', include('User.urls')),
    path('base/', include('Base.api_urls')),
    path('app/', include('App.urls')),
    path('oauth/', include('OAuth.urls')),
    path('wechat/', include('Wechat.api_urls')),
]
