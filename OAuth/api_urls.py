from django.urls import path

from OAuth.api_views import OAuthView, OAuthTokenView

urlpatterns = [
    path('', OAuthView.as_view()),
    path('token', OAuthTokenView.as_view()),
]
