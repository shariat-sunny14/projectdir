from django.urls import path
from . import views

urlpatterns = [
    path('students_registration_services/', views.RegistrationServicesManagerAPI, name='students_registration_services'),
    path('add_registration_modal/', views.addRegistrationModelManageAPI, name="add_registration_modal"),
    path('edit_registration_modal/', views.editRegistrationModelManageAPI, name='edit_registration_modal'),
    path('active_registration/', views.activeRegistrationManagerAPI, name='active_registration'),
    path('active_reg_submission/', views.activeRegSubmissionAPI, name='active_reg_submission'),
    path('inactive_registration/', views.inactiveRegistrationManagerAPI, name='inactive_registration'),
    # restriction
    path('restriction_registration/', views.restrictionRegistrationManagerAPI, name='restriction_registration'),
    # 
    path('inactive_reg_submission/', views.inactiveRegSubmissionAPI, name='inactive_reg_submission'),
    path('save_update_customer_registrations/', views.saveRegistrationsAPI, name="save_update_customer_registrations"),
    path('get_customer_registration_list/', views.getCustomerRegistrationsListAPI, name="get_customer_registration_list"),
    path('search_registration_for_billing/', views.searchCustomerRegistrationAPI, name="search_registration_for_billing"),
    path('select_registrations_details/', views.selectCustomerRegistrationDtlsAPI, name="select_registrations_details"),
    path('get_optional_subjects_option/', views.getOptionalSubjectsManagerAPI, name="get_optional_subjects_option"),
    # restriction confirm submission
    path('restriction_confirm_submission/', views.restrictionConfirmSubmissionAPI, name="restriction_confirm_submission"),
]
