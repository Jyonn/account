from django.urls import path

from App.api_views import AppView, AppIDView, ScopeView, AppLogoView, UserAppIdView, \
    AppIDSecretView, refresh_frequent_score, PremiseView

urlpatterns = [
    path('', AppView.as_view()),
    path('scope', ScopeView.as_view()),
    path('premise', PremiseView.as_view()),
    path('logo', AppLogoView.as_view()),
    path('@refresh-frequent-score', refresh_frequent_score),

    path('user/<str:user_app_id>', UserAppIdView.as_view()),
    path('<str:app_id>', AppIDView.as_view()),
    path('<str:app_id>/secret', AppIDSecretView.as_view()),
]
