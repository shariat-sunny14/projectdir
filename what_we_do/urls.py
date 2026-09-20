# what_we_do/urls.py
from django.urls import path
from . import views

app_name = 'what_we_do'

urlpatterns = [
    path('service_home/', views.service_home, name='service_home'),
    path('service/<int:pk>/edit/', views.service_edit, name='service_edit'),
    path('service/<int:pk>/delete/', views.service_delete, name='service_delete'),
]