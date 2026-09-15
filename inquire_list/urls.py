from django.urls import path
from . import views

urlpatterns = [
    path('inquire_list/', views.inquireListViewManagerAPI, name='inquire_list'),
    path('inquires_listed/', views.inquireListViewFromWebsiteManagerAPI, name='inquires_listed'),
    path('get_inquire_list/', views.getInquireListManagerAPI, name='get_inquire_list'),
    path('view_inquire_modal/', views.viewInquireModalManagerAPI, name='view_inquire_modal'),
    path('save_inquire_api/', views.saveInquireManagerAPI, name='save_inquire_api'),
]
