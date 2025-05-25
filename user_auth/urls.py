from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # path('accounts/login/', auth_views.LoginView.as_view(template_name='logger/singin_form.html', redirect_authenticated_user=True), name="login"),
    path('accounts/login/', views.user_loginManagerAPI, name='login'),
    path('user_wise_login/', views.user_loginAPI, name='user_wise_login'),
    path('', views.main_dashboard, name='main_dashboard'),
    path('accounts/profile/', views.main_dashboard, name='main_dashboard'),
    path('user/logout/', views.logoutuser, name='logout'),
    path('fetch_organizations_list/', views.fetch_organizations, name='fetch_organizations_list'),
    path('statistics_dashboard/', views.statisticsManagerAPI, name='statistics_dashboard'),
    path('get_user_org_informations/', views.getUserInfoAPI, name='get_user_org_informations'),
    path('logout-all/', views.logout_all_users, name='logout_all_users'),
    # 
    path('testlogin', views.testLogin, name='testlogin'),
]
