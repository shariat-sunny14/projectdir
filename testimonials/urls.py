from django.urls import path
from . import views

app_name = "testimonials"

urlpatterns = [
    # ---- Public ----
    path("submit/", views.testimonial_create, name="create"),
    path("api/list/", views.testimonial_list_api, name="api_list"),

    # ---- Staff dashboard (CRUD UI) ----
    path("testimonials_list/", views.dashboard_list, name="dashboard_list"),
    path("add_testimonials/", views.dashboard_add, name="dashboard_add"),
    path("<int:pk>/edit/", views.dashboard_edit, name="dashboard_edit"),
    path("<int:pk>/delete/", views.dashboard_delete, name="dashboard_delete"),
    path("<int:pk>/toggle-approve/", views.dashboard_toggle_approve, name="dashboard_toggle_approve"),
]