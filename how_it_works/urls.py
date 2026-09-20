from django.urls import path

from . import views

app_name = "how_it_works"

urlpatterns = [
    path("how_it_workst/", views.how_it_workstAPI, name="how_it_workst"),
    path("section/edit/", views.section_edit, name="section_edit"),
    path("step/add/", views.step_create, name="step_create"),
    path("step/<int:pk>/edit/", views.step_update, name="step_update"),
    path("step/<int:pk>/delete/", views.step_delete, name="step_delete"),
]
