from django.urls import path
from . import views

urlpatterns = [
    path('facebook_posts/', views.facebook_posts, name='facebook_posts'),
    path('facebook_posts_sync/', views.facebook_posts_sync, name='facebook_posts_sync'),
    path('facebook_settings/', views.facebook_settings, name='facebook_settings'),
    path('sync_facebook/', views.sync_facebook, name='sync_facebook'),
]