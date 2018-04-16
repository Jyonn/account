from django.urls import path

from App.views import AppView

urlpatterns = [
    path('apply', AppView.apply, name="app-apply"),
    path('info-modify/<str:app_id>', AppView.info_modify, name="app-info-modify"),
]
