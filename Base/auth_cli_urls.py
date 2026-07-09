from django.urls import path

from Base import auth_cli_views


urlpatterns = [
    path('device/start', auth_cli_views.AuthCLIDeviceStartView.as_view()),
    path('device/poll', auth_cli_views.AuthCLIDevicePollView.as_view()),
    path('device', auth_cli_views.AuthCLIDeviceView.as_view()),
    path('device/confirm', auth_cli_views.AuthCLIDeviceConfirmView.as_view()),
]
