from django.urls import path
from . import views

urlpatterns = [

    path('about/', views.about_page, name='about'),
    
    # ABOUT US
    path('about/add/', views.about_add, name='about_add'),
    path('about/edit/<int:pk>/', views.about_edit, name='about_edit'),
    path('about/delete/<int:pk>/', views.about_delete, name='about_delete'),

    # LIFE
    path('life/add/', views.life_add, name='life_add'),
    path('life/edit/<int:pk>/', views.life_edit, name='life_edit'),
    path('life/delete/<int:pk>/', views.life_delete, name='life_delete'),

    # TEAM
    path('team/add/', views.team_add, name='team_add'),
    path('team/edit/<int:pk>/', views.team_edit, name='team_edit'),
    path('team/delete/<int:pk>/', views.team_delete, name='team_delete'),

    # AWARD
    path('award/add/', views.award_add, name='award_add'),
    path('award/edit/<int:pk>/', views.award_edit, name='award_edit'),
    path('award/delete/<int:pk>/', views.award_delete, name='award_delete'),

    # CERTIFICATE
    path('certificate/add/', views.certificate_add, name='certificate_add'),
    path('certificate/edit/<int:pk>/', views.certificate_edit, name='certificate_edit'),
    path('certificate/delete/<int:pk>/', views.certificate_delete, name='certificate_delete'),
]