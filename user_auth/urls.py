from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.websitesManagerAPI, name='websites'),
    path('web/sites/', views.websitesManagerAPI, name='websites'),
    path('accounts/login/', views.user_loginManagerAPI, name='login'),
    path('user_wise_login/', views.user_loginAPI, name='user_wise_login'),
    # path('', views.main_dashboard, name='main_dashboard'),
    path('accounts/profile/', views.main_dashboard, name='main_dashboard'),
    path('user/logout/', views.logoutuser, name='logout'),
    path('logout-all/', views.logout_all_users, name='logout_all_users'),
    # 
    path('org_info_setup/', views.orgInfoManagerAPI, name='org_info_setup'),
    path('org_add_update/', views.organization_addupdateAPI, name='org_add_update'),
    path('get_org_info_data/', views.organization_getAPI, name='get_org_info_data'),
    # 
    path('testlogin', views.testLogin, name='testlogin'),
    # password verification and reset
    path('send-reset-otp/', views.send_reset_otp, name='send_reset_otp'),
    path('verify-reset-otp/', views.verify_reset_otp, name='verify_reset_otp'),
    path('change-password/', views.change_password, name='change_password'),
    # registration
    path('register_user/', views.register_user_managerAPI, name='register_user'),
]
