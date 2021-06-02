from django.urls import path

from OAuth import views

urlpatterns = [
    path('', views.OAuth.as_view()),
    path('token', views.OAuthToken.as_view()),
]
