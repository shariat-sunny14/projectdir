from django.urls import path
from . import views

urlpatterns = [
    path('apps_templates_manager/', views.billTemplateManagerAPI, name='apps_templates_manager'),
    path('save_apps_templates/', views.saveAppsTemplateManagerAPI, name='save_apps_templates'),
    path('get_apps_temp_options/', views.getBillTempOptionManagerAPI, name='get_apps_temp_options'),
]