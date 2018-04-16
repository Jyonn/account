from django.urls import path

from App.api_views import AppView, AppIDView, ScopeView, AppLogoView

urlpatterns = [
    path('', AppView.as_view()),
    path('scope', ScopeView.as_view()),
    path('logo', AppLogoView.as_view()),
    path('<str:app_id>', AppIDView.as_view()),
]
