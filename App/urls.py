from django.urls import path

from App import views

urlpatterns = [
    path('', views.AppV.as_view()),
    path('list', views.AppList.as_view()),
    path('scope', views.ScopeV.as_view()),
    path('premise', views.PremiseV.as_view()),
    path('logo', views.AppLogo.as_view()),
    path('@refresh-frequent-score', views.refresh_frequent_score),
    path('@fix-user-num', views.fix_user_num),

    path('user/<str:user_app_id>', views.UserAppId.as_view()),
    path('<str:app_id>', views.AppID.as_view()),
    path('<str:app_id>/secret', views.AppIDSecret.as_view()),
]
