from django.urls import path
from . import views

urlpatterns = [
    path('advertisment_item_list/', views.advertisementItemAPI, name='advertisment_item_list'),
    path('new_add_advert_item_modal/', views.newAddAdvertItemModalAPI, name='new_add_advert_item_modal'),
    path('save_advert_item/', views.saveAdvertItemAPI, name='save_advert_item'),
    path('edit_advert_item_modal/', views.editAdvertItemModalAPI, name='edit_advert_item_modal'),
    path('edit_save_advert_item/', views.editSaveAdvertItemAPI, name='edit_save_advert_item'),
    path('delete_advert_item/', views.deleteAdvertItemAPI, name='delete_advert_item'),
]
