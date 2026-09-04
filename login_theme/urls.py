from django.urls import path
from . import views

urlpatterns = [
    path('login_themes_manager/', views.loginThemeSetupManagerAPI, name='login_themes_manager'),
    path('save_update_login_theme/', views.saveUpdateLoginThemeTemplatesAPI, name='save_update_login_theme'),
]
