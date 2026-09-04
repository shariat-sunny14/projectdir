from django.urls import path
from . import views

urlpatterns = [
    path('enroll_setup_list/', views.enrollSetupListManagerAPI, name='enroll_setup_list'),
    path('add_new_enroll_modal/', views.addNewEnrollModalManageAPI, name='add_new_enroll_modal'),
    path('save_enroll_setup_api/', views.saveEnrollSetupManagerAPI, name='save_enroll_setup_api'),
    path('edit_enroll_modal/', views.editEnrollUsModalManageAPI, name='edit_enroll_modal'),
    path('delete_enroll_list/', views.deleteEnrollListManagerAPI, name='delete_enroll_list'),
    path('delete_enroll_details/', views.delete_EnrollDetails_edit_modeAPI, name='delete_enroll_details'),
    path('show_enroll_details_modal/<int:enroll_id>/', views.showEnrollDetailsModalManageAPI, name="show_enroll_details_modal"),
    path('enroll_from_booking', views.enroll_from_booking, name='enroll_from_booking'),
    path('save_enroll_booking', views.save_enroll_booking, name='save_enroll_booking'),
    path('enroll_listed', views.enrollListViewFromWebsiteManagerAPI, name='enroll_listed'),
    path('get_enroll_booking_list', views.get_enroll_booking_list, name='get_enroll_booking_list'),
]
