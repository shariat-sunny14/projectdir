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
    # ... apnar existing url patterns ...
    path('api/gallery-list/', views.gallery_list_ajax, name='gallery_list_ajax'),
    path('api/photo-types/', views.photo_types_ajax, name='photo_types_ajax'),
    path('api/gallery-detail/<int:phgallery_id>/', views.gallery_detail_ajax, name='gallery_detail_ajax'),
    # 
    path('api/services-gallery/', views.services_gallery_ajax, name='services_gallery_ajax'),
    path('api/albums-list/', views.albums_list, name='albums_list'),
    path('api/albums-detail/<int:phgallery_id>/', views.albums_detail, name='albums_detail'),  # ✅ notun
    path('api/photogallery-list/', views.photogallery_list, name='photogallery_list'),
]
