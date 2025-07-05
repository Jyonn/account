from django.urls import path

from App import views

urlpatterns = [
    path('', views.AppView.as_view()),
    path('list', views.AppListView.as_view()),
    path('scope', views.ScopeView.as_view()),
    path('premise', views.PremiseView.as_view()),
    path('logo', views.AppLogoView.as_view()),
    path('@refresh-frequent-score', views.FrequencyRefreshView.as_view()),
    path('@fix-user-num', views.UserNumView.as_view()),

    path('user/<str:user_app_id>', views.UserAppIdView.as_view()),
    path('<str:app_id>', views.AppID.as_view()),
    path('<str:app_id>/secret', views.AppIDSecret.as_view()),
]
