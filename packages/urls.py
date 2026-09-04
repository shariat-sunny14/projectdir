from django.urls import path
from . import views

urlpatterns = [
    path('packages_head_body_manager/', views.packagesHeadBodyManagerAPI, name='packages_head_body_manager'),
    path('save_update_packages_head_body/', views.saveUpdatePackagesHeadBodyManager, name='save_update_packages_head_body'),
    path('packages_setup/', views.packagesSetupManagerAPI, name='packages_setup'),
    path('add_package_setup_api/', views.addPackageSetupmanagerAPI, name='add_package_setup_api'),
    path('delete_package_list/', views.deletePackageListManagerAPI, name="delete_package_list"),
    # packages details
    path('packages_details/', views.packagesDetailsManagerAPI, name="packages_details"),
    path('add_new_package_modal/', views.addNewPackageModalManageAPI, name="add_new_package_modal"),
    path('edit_package_modal/', views.editPackageModalManageAPI, name="edit_package_modal"),
    path('show_package_details_modal/<int:package_id>/', views.showPackageDetailsModalManageAPI, name="show_package_details_modal"),
    path('delete_packages_dtls_edit_mode/', views.delete_packages_dtls_edit_modeAPI, name="delete_packages_dtls_edit_mode"),
]
