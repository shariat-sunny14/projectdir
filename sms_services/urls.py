from django.urls import path
from . import views

urlpatterns = [
    path('sms_services_lists/', views.smsListManagerAPI, name='sms_services_lists'),
    path('get_sms_send_list/', views.getSMSSendListManagerAPI, name='get_sms_send_list'),
    path('get_sms_complete_list/', views.getSMSCompleteListManagerAPI, name='get_sms_complete_list'),
    path('send_sms_services/', views.sendSMSManagerAPI, name='send_sms_services'),
    path('sending_sms_api/', views.sendingSMSManagerAPI, name='sending_sms_api'),
    path('send_sms_completed_services/', views.sendSMSCompletedManagerAPI, name='send_sms_completed_services'),
]