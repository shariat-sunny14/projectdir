from django.urls import path
from . import views

urlpatterns = [
    path('why_us/', views.whyUsManagerAPI, name='why_us'),
    # Admin CRUD
    path('faq_list/', views.faq_list, name='faq_list'),
    path('faq_create/', views.faq_create, name='faq_create'),
    path('faq_update/<int:id>/', views.faq_update, name='faq_update'),
    path('faq_delete/<int:id>/', views.faq_delete, name='faq_delete'),
]
