from django.urls import path
from . import views

urlpatterns = [
    path('featured_gallery_details/<int:phgallery_id>/', views.featuredGalleryDtlsManagerAPI, name='featured_gallery_details'),
    path('add_new_photo_gallery_list/', views.addNewPhotoGalleryListManagerAPI, name='add_new_photo_gallery_list'),
    path('add_new_photo_gallery_modal/', views.addNewPhotoGalleryModalManageAPI, name='add_new_photo_gallery_modal'),
    path('add_new_photo_gallery_details/', views.addNewPhotoGalleryDetailsManagerAPI, name='add_new_photo_gallery_details'),
    path('get_photo_gallery_list/', views.get_photo_gallery_listAPI, name='get_photo_gallery_list'),
    path('edit_photo_gallery_modal/', views.editNewPhotoGalleryModalManageAPI, name='edit_photo_gallery_modal'),
    path('delete_dtls_photo_edit_mode/', views.delete_dtls_photo_edit_modeAPI, name='delete_dtls_photo_edit_mode'),
    path('delete_gallery/', views.delete_galleryAPI, name='delete_gallery'),
]
