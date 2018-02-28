from django.urls import path

from User.views import UserView as View

urlpatterns = [
    path('register', View.register, name="register"),
]
