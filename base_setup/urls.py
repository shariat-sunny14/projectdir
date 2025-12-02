from django.urls import path
from . import views

urlpatterns = [
    path('examination_category_setup_services/', views.baseSetupManagerAPI, name='examination_category_setup_services'),
]