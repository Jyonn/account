from django.urls import path

from Base import auth_v2_views


urlpatterns = [
    path('session', auth_v2_views.AuthV2SessionView.as_view()),
    path('captcha', auth_v2_views.AuthV2CaptchaView.as_view()),
    path('password', auth_v2_views.AuthV2PasswordView.as_view()),
    path('code/send', auth_v2_views.AuthV2CodeSendView.as_view()),
    path('code/verify', auth_v2_views.AuthV2CodeVerifyView.as_view()),
]
