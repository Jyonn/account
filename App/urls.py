from django.urls import path

from App.views import AppView

urlpatterns = [
    path('apply', AppView.apply, name="app-apply")
]
