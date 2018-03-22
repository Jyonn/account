from django.urls import path

from App.api_views import AppView, AppIDView

urlpatterns = [
    path('', AppView.as_view()),
    path('<str:app_id>', AppIDView.as_view()),
]
