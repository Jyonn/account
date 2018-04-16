from django.urls import path

from OAuth.views import OAuthView

urlpatterns = [
    path('', OAuthView.oauth, name="user-oauth"),
]
