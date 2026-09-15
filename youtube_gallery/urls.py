from django.urls import path
from . import views

urlpatterns = [
    path('video_list/', views.video_list, name='video_list'),
    path('add/', views.video_add, name='video_add'),
    path('edit/<int:pk>/', views.video_edit, name='video_edit'),
    path('delete/<int:pk>/', views.video_delete, name='video_delete'),
]