from django.urls import path
from . import views

urlpatterns = [
    path('class_wise_tabulation_list/', views.reportTabulationListManagerAPI, name='class_wise_tabulation_list'),
    path('get_sections_by_class/', views.getSectionsByClassManagerAPI, name='get_sections_by_class'),
    path('half_yearly_tabulation_reports/', views.halfYearlyTabulationReportsManagerAPI, name='half_yearly_tabulation_reports'),
    path('half_yearly_tabulation_reports_api/', views.halfYearlyTabulationReportsAPI, name='half_yearly_tabulation_reports_api'),
]